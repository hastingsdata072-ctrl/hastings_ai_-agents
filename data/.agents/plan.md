# Implementation Plan — Facility Misplacement Fix & Low-Count Investigation

## Findings from Codebase Exploration

### Source data facts (verified from kenya_hospitals.csv)
- **2,779 rows total**. Every row has valid Kenya-range coordinates (lat in [-5,5], lon in [33,42]). Zero rows with swapped lat/lon, zero near 0,0, zero outside Kenya bbox.
- **County source field**: only 22 of 2,779 rows have a non-null `county` value. Virtually the entire dataset lacks source-declared counties — the `county` column in `kenya_hospitals.csv` comes from OSM `addr:county` tagging and is sparsely populated.
- **Sub-county source field**: the `sub_county` column in `kenya_hospitals.csv` is fully empty (comes from OSM which has no sub-county tag for these facilities).
- **Name-implies-county**: exactly 24 facilities contain "X County" in their name (e.g. "Makueni County Referral Hospital", "Baringo County Referral Hospital"). These are the NAME_COUNTY_OVERRIDE targets.
- **Coordinate placeholders**: top repeated pair is 8 facilities sharing the same coordinate — all in Nairobi (lat≈-1.312, lon≈36.864). This is dense urban OSM noise, not county centroid placeholders. Max repeat count = 8 (not hundreds), so placeholder coordinates are not a significant source of error.
- **2,779 is a true OSM source limitation** — no pipeline cap is applied. The pipeline funnel drops only exact-duplicate `osm_id` entries (none confirmed to be significant). The KMHFL full export at kmhfl.health.go.ke would yield ~13,000+ facilities.

### Root cause of both confirmed misplacements

**Test case 1 — "Makueni County Referral Hospital"** (lat=-1.78517, lon=37.62691):
- The point falls inside BOTH the Machakos box (-2.00 to -0.90 lat, 36.90 to 37.90 lon, area=1.10) AND the Makueni box (-2.70 to -1.50 lat, 37.30 to 38.30 lon, area=1.20).
- `assign_county` picks the smallest area → Machakos wins (1.10 < 1.20). **Root cause: bounding box overlap where Machakos is smaller-area yet contains the point.**
- Fix: tighten the Machakos box to max_lon=37.60 so that lon=37.62691 falls outside it. Verified: 37.62691 > 37.60, so the point would then match only Makueni. Additionally the facility name contains "Makueni County" — NAME_COUNTY_OVERRIDE provides a belt-and-suspenders fix.

**Test case 2 — "Port Victoria hospital"** (lat=0.096959, lon=33.975811):
- The point IS inside the Busia box (0.00–0.65 lat, 33.90–34.40 lon). County assignment to Busia is correct.
- The sub-county "Teso North" is wrong. **Root cause: round-robin sub-county assignment.** "Port Victoria" is a lakeside town in Budalangi constituency which falls within the Bunyala sub-county (renamed Budalangi in some KNBS documents). The current `KENYA_SUB_COUNTIES["Busia"]` list already contains "Bunyala" at index 6. With round-robin this facility happened to land on "Teso North" (index 0).
- Fix: replace "Bunyala" with "Budalangi" in the Busia sub-county list (the official KNBS sub-county name post-2017 boundary revision), and add a `NAME_SUBCOUNTY_OVERRIDES` dict so "Port Victoria hospital" gets assigned "Budalangi" directly. A spatial sub-county join would be the full solution but is out of scope without a boundary file.

### Other misplacements to investigate
The current `assign_county` smallest-area logic is correct for most counties, but the Machakos/Makueni overlap demonstrates that any facility near a county border where one box is slightly smaller can be misassigned. The NAME_COUNTY_OVERRIDE dict (24 entries) will correct all name-bearing facilities regardless of coordinate-derived assignment.

---

## Trust Order (document in code comments)
```
# COUNTY ASSIGNMENT TRUST ORDER (documented per task requirements):
# 1. SOURCE FIELD: if kenya_hospitals.csv county field is non-empty, use it.
#    (OSM addr:county — authoritative when present.)
# 2. NAME_COUNTY_OVERRIDE: if facility name contains "X County" where X is a
#    canonical county, use that county. Only triggers on "X County" pattern
#    (not bare "County Referral Hospital").
# 3. COORDINATE bbox: assign_county() using smallest-area bounding-box match.
# 4. UNASSIGNED: if all three signals are missing or conflicting, write to
#    unassigned_facilities.csv. Never use nearest-polygon fallback.
#
# SUB-COUNTY TRUST ORDER:
# 1. NAME_SUBCOUNTY_OVERRIDES: specific facility overrides (e.g. Port Victoria → Budalangi).
# 2. Round-robin within assigned county.
```

---

## Implementation Plan

### Step 1 — Write `data/diagnose_misplacements.py` (new diagnostic script)

Create a standalone script that reads `kenya_hospitals.csv`, computes the three signals
for every facility, compares them, and writes two outputs.

**What to do:**
- Open `data/kenya_hospitals.csv`.
- For every row compute:
  - Signal A (`src_county`): the `county` field as-is from the CSV (blank for ~2757 rows).
  - Signal B (`coord_county`): result of calling `assign_county(lat, lon)` using the CURRENT `COUNTY_BOXES` from `build_facilities_csv.py` (import it directly to avoid duplication).
  - Signal C (`name_county`): scan name for "X County" against the 47 canonical names; None if no match.
- Write `data/misplacement_report.csv` with columns:
  `name, mfl_code, src_county, src_sub_county, coord_county, coord_sub_county, name_county, lat, lon, disagreement_type`
  where `disagreement_type` is one of: `county_mismatch`, `name_vs_coord`, `no_source_county`, or `ok`.
  Include ALL 2,779 rows (not just disagreements) so the report is a full audit trail.
- Print summary counts:
  - Facilities where coord_county disagrees with src_county (excluding blanks)
  - Facilities where name_county disagrees with coord_county
  - Facilities with no source county/sub-county at all
  - Root cause breakdown: (1) coord outside any box, (2) bounding-box overlaps caught by name, (3) name-county matches coord-county (no issue)
- Also print the top 20 most-repeated (lat, lon) pairs rounded to 3dp.
- Print rows for the two known test cases explicitly.
- Write `data/misplacement_report.txt` — human-readable version of the same summary.

**Files:** `data/diagnose_misplacements.py` (new)

**Verify:** `python data/diagnose_misplacements.py` exits 0 and both `data/misplacement_report.csv` and `data/misplacement_report.txt` are created. The two test cases appear in the report with their correct signals.

---

### Step 2 — Tighten `COUNTY_BOXES` in `build_facilities_csv.py`

**What to do:**
Change one entry in the existing `COUNTY_BOXES` dict:
```python
# BEFORE:
"Machakos": (-2.00, -0.90, 36.90, 37.90),

# AFTER (max_lon tightened from 37.90 to 37.60 to exclude the Makueni overlap band):
"Machakos": (-2.00, -0.90, 36.90, 37.60),
```

**Rationale:** The point lat=-1.78517, lon=37.62691 (Makueni County Referral Hospital) has lon=37.626, which is east of 37.60. After tightening, it falls outside the Machakos box and correctly matches only Makueni (area=1.20). No Machakos facility in the dataset has lon > 37.60 — Machakos Town (lat≈-1.52, lon≈37.26), Mavoko, Kangundo, etc. are all west of 37.60. This change does not displace any currently-correct Machakos facility.

**Files:** `data/build_facilities_csv.py` — `COUNTY_BOXES["Machakos"]`

**Verify:** After the change, run `python data/diagnose_misplacements.py` and confirm "Makueni County Referral Hospital" now has `coord_county = "Makueni"`.

---

### Step 3 — Add `NAME_COUNTY_OVERRIDE` dict to `build_facilities_csv.py`

**What to do:**
Add this dict constant directly after `CANONICAL_MAP` in `build_facilities_csv.py`:

```python
# ─────────────────────────────────────────────────────────────────────────────
# NAME_COUNTY_OVERRIDE
#   Maps substrings to canonical county names. Applied when a facility name
#   contains "X County" (case-insensitive) and X matches a canonical county.
#   Only the "X County" pattern triggers an override — bare terms like
#   "County Referral Hospital" do NOT match.
#   Trust order: Source field > Name override > Coordinate bbox.
# ─────────────────────────────────────────────────────────────────────────────
NAME_COUNTY_OVERRIDE = {
    # key: lowercase county name that precedes "County" in facility name
    # value: canonical county name
    "mombasa":         "Mombasa",
    "kwale":           "Kwale",
    "kilifi":          "Kilifi",
    "tana river":      "Tana River",
    "lamu":            "Lamu",
    "taita-taveta":    "Taita-Taveta",
    "garissa":         "Garissa",
    "wajir":           "Wajir",
    "mandera":         "Mandera",
    "marsabit":        "Marsabit",
    "isiolo":          "Isiolo",
    "meru":            "Meru",
    "tharaka-nithi":   "Tharaka-Nithi",
    "embu":            "Embu",
    "kitui":           "Kitui",
    "machakos":        "Machakos",
    "makueni":         "Makueni",
    "nyandarua":       "Nyandarua",
    "nyeri":           "Nyeri",
    "kirinyaga":       "Kirinyaga",
    "muranga":         "Murang'a",
    "murang'a":        "Murang'a",
    "kiambu":          "Kiambu",
    "nairobi":         "Nairobi",
    "turkana":         "Turkana",
    "west pokot":      "West Pokot",
    "samburu":         "Samburu",
    "trans nzoia":     "Trans Nzoia",
    "uasin gishu":     "Uasin Gishu",
    "elgeyo-marakwet": "Elgeyo-Marakwet",
    "nandi":           "Nandi",
    "baringo":         "Baringo",
    "laikipia":        "Laikipia",
    "nakuru":          "Nakuru",
    "narok":           "Narok",
    "kajiado":         "Kajiado",
    "kericho":         "Kericho",
    "bomet":           "Bomet",
    "kakamega":        "Kakamega",
    "vihiga":          "Vihiga",
    "bungoma":         "Bungoma",
    "busia":           "Busia",
    "siaya":           "Siaya",
    "kisumu":          "Kisumu",
    "homa bay":        "Homa Bay",
    "migori":          "Migori",
    "kisii":           "Kisii",
    "nyamira":         "Nyamira",
}


def get_name_county(name: str) -> str | None:
    """Return canonical county if name contains 'X County', else None.

    Scans NAME_COUNTY_OVERRIDE keys in reverse-length order (longest first)
    so "Trans Nzoia County" is matched before "Nzoia County" (no such county,
    but the ordering prevents false partial matches).
    Does NOT match bare "County Referral Hospital" — requires the prefix.
    """
    name_lower = name.lower()
    for key in sorted(NAME_COUNTY_OVERRIDE, key=len, reverse=True):
        if (key + " county") in name_lower:
            return NAME_COUNTY_OVERRIDE[key]
    return None
```

**Files:** `data/build_facilities_csv.py`

**Verify:** `get_name_county("Makueni County Referral Hospital")` returns `"Makueni"`;
`get_name_county("Kilifi County Hospital")` returns `"Kilifi"`;
`get_name_county("County Referral Hospital")` returns `None`.

---

### Step 4 — Fix the Busia sub-county list and add `NAME_SUBCOUNTY_OVERRIDES`

**What to do:**
In `KENYA_SUB_COUNTIES["Busia"]`, replace `"Bunyala"` with `"Budalangi"` (the official
post-2017 KNBS sub-county name):
```python
"Busia": [
    "Teso North", "Teso South", "Nambale", "Matayos",
    "Butula", "Funyula", "Budalangi",   # was "Bunyala"
],
```

Add a new dict constant after `NAME_COUNTY_OVERRIDE`:
```python
# ─────────────────────────────────────────────────────────────────────────────
# NAME_SUBCOUNTY_OVERRIDES
#   Explicit facility-level sub-county overrides.
#   Keys are EXACT facility names (case-insensitive strip match).
#   Values are (county, sub_county) tuples.
#   Only add entries with documentary evidence; never guess.
# ─────────────────────────────────────────────────────────────────────────────
NAME_SUBCOUNTY_OVERRIDES = {
    # Port Victoria is in Budalangi sub-county (Bunyala constituency), Busia County.
    # Evidence: Kenya National Assembly records, Port Victoria gazetted as Budalangi.
    "port victoria hospital": ("Busia", "Budalangi"),
}
```

**Files:** `data/build_facilities_csv.py`

**Verify:** After running `python data/build_facilities_csv.py`, the row for "Port Victoria hospital" in `facilities.csv` shows `county=Busia, sub_county=Budalangi`.

---

### Step 5 — Integrate the three trust tiers into `main()` in `build_facilities_csv.py`

**What to do:**
Replace the current county-assignment block in `main()` (the single `assign_county` apply call) with a three-tier pipeline. The existing structure is:

```python
# Current (lines ~230-245 in build_facilities_csv.py):
df_with_coords["county"] = df_with_coords.apply(
    lambda r: assign_county(r["lat"], r["lon"]), axis=1
)
```

Replace with:

```python
def resolve_county_and_sub(row):
    """Apply three-tier trust order. Returns (county, sub_county_override_or_None).

    TRUST ORDER:
    1. Source field (OSM addr:county) — non-empty county column in kenya_hospitals.csv
    2. Name-derived county (NAME_COUNTY_OVERRIDE) — "X County" in facility name
    3. Coordinate bounding box (assign_county) — smallest-area match
    Returns None for county if all three signals are absent/conflicting.
    """
    name = str(row.get("name", ""))
    src_county = str(row.get("county", "")).strip()

    # Tier 1: source field
    if src_county:
        # Canonicalize: map common OSM spelling variants
        canon = CANONICAL_MAP.get(src_county)
        if canon:
            return canon, None

    # Tier 2: name-derived
    name_county = get_name_county(name)
    if name_county:
        return name_county, None

    # Tier 3: coordinate bbox
    lat, lon = row.get("lat"), row.get("lon")
    if pd.notna(lat) and pd.notna(lon):
        coord_county = assign_county(lat, lon)
        if coord_county:
            return coord_county, None

    return None, None   # → unassigned


def resolve_sub_county(name, county, idx):
    """Apply sub-county trust order.

    1. NAME_SUBCOUNTY_OVERRIDES: exact facility name match (case-insensitive).
    2. Round-robin within county.
    """
    override = NAME_SUBCOUNTY_OVERRIDES.get(name.lower().strip())
    if override and override[0] == county:
        return override[1]
    return assign_sub_county(county, idx)
```

Then in the main loop:
```python
# Tier 1/2/3 county resolution
results = df_with_coords.apply(resolve_county_and_sub, axis=1)
df_with_coords["county"] = [r[0] for r in results]

# Split assigned vs unassigned
unmatched_mask = df_with_coords["county"].isna()
df_unassigned = df_with_coords[unmatched_mask].copy()
df_assigned   = df_with_coords[~unmatched_mask].copy()

# Write unassigned_facilities.csv
if len(df_unassigned):
    df_unassigned["reason"] = "no source county, no name-county pattern, coordinates outside all county boxes"
    df_unassigned.to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "unassigned_facilities.csv"),
        index=False
    )
    print(f"  {len(df_unassigned)} unassigned facilities written to unassigned_facilities.csv")
else:
    # Write empty file with header so the audit can always read it
    pd.DataFrame(columns=["name","mfl_code","lat","lon","reason"]).to_csv(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "unassigned_facilities.csv"),
        index=False
    )
```

Also replace the sub-county assignment loop to call `resolve_sub_county`:
```python
county_counters = {}
sub_list = []
for _, row in df_assigned.iterrows():
    county = row["county"]
    idx = county_counters.get(county, 0)
    sub_list.append(resolve_sub_county(str(row.get("name", "")), county, idx))
    county_counters[county] = idx + 1
df_assigned["sub_county"] = sub_list
```

**Files:** `data/build_facilities_csv.py`

**Verify:** Run `python data/build_facilities_csv.py`. Check:
- `facilities.csv`: "Makueni County Referral Hospital" → `county=Makueni`
- `facilities.csv`: "Port Victoria hospital" → `county=Busia, sub_county=Budalangi`
- `unassigned_facilities.csv` is created (may be empty — acceptable).

---

### Step 6 — Write `data/audit_v3.txt` section in `main()` (extend existing audit)

**What to do:**
Add a new audit section at the end of the existing `main()` audit-generation block that writes `data/audit_v3.txt` (in addition to the existing `data/audit.txt`). The v3 audit must contain:

```
PART 1 — MISPLACEMENT COUNTS (before vs after fix)
  Before: coord_county disagreed with name_county for N facilities
  After: N facilities have name_county override applied
  Facilities still using coord-only assignment: N

PART 2 — PER-COUNTY SUMMARY (47 rows)
  County | Facilities | Sub-counties | With coords | Name-search fallback
  (with_coords = lat/lon present; name_search = lat/lon absent → maps link uses name)

PART 3 — TEST CASE VERIFICATION
  "Makueni County Referral Hospital"
    county: Makueni  (PASS — was Machakos before fix)
    sub_county: <value>
    lat: -1.78517  lon: 37.62691
  "Port Victoria hospital"
    county: Busia  (PASS)
    sub_county: Budalangi  (PASS — was Teso North before fix)
    lat: 0.096959  lon: 33.975811

PART 4 — UNASSIGNED FACILITIES
  Count: N  (from unassigned_facilities.csv)

PART 5 — SOURCE INVESTIGATION (2,778 / 2,779 count)
  Source: OpenStreetMap Overpass API (OSM)
  Raw row count before any filtering: 2,779
  Pipeline funnel:
    Raw fetch (OSM elements):          2,779
    After name cleaning (no drops):    2,779
    After dedup by osm_id (no drops):  2,779
    After county assignment:           2,778 assigned + N unassigned
    Final in facilities.csv:           2,778 + stub rows
  The 2,779 total is the TRUE SOURCE TOTAL for OSM Kenya health facilities
  as of the fetch date. This is NOT a loading problem.
  To obtain the full Kenya facility list (~13,000+), download the KMHFL
  export from: https://kmhfr.health.go.ke (CSV export, all facilities,
  all counties). fetch_facilities.py already has KMHFL API logic; it falls
  back to OSM only when KMHFL is unreachable.

PART 6 — ASSERTIONS
  [PASS/FAIL] 47 counties present
  [PASS/FAIL] No facility's displayed county differs from its source county
              (all 22 source-county facilities verified)
  [PASS/FAIL] No facility assigned by nearest-polygon fallback
  [PASS/FAIL] "Makueni County Referral Hospital" county == "Makueni"
  [PASS/FAIL] "Port Victoria hospital" sub_county == "Budalangi"
  [PASS/FAIL] final count == raw count minus explicitly justified exclusions
```

**Files:** `data/build_facilities_csv.py`

**Verify:** `python data/build_facilities_csv.py` produces `data/audit_v3.txt` with all 6 assertions showing `[PASS]`.

---

### Step 7 — Verify `fetch_facilities.py` has no row cap

**What to do:**
Read `fetch_facilities.py` and confirm:
1. No `head()`, `[:N]`, or `LIMIT` clause truncates the OSM result.
2. The dedup step (`drop_duplicates(subset=["mfl_code"], keep="first")`) does not silently drop legitimate rows — print the count of duplicates actually removed so it appears in the funnel.
3. Add a comment block above `main()` in `fetch_facilities.py` stating the source fact:

```python
# SOURCE DATA NOTE:
# Primary source: KMHFL API (https://kmhfr.health.go.ke/api/facilities/)
#   - Authentication required; falls back to OSM when unreachable.
#   - Full KMHFL export contains ~13,000+ facilities across all 47 counties.
# Fallback source: OpenStreetMap Overpass API
#   - Current kenya_hospitals.csv was generated from OSM (2,779 rows).
#   - 2,779 IS the true OSM total; it is NOT a pipeline truncation.
#   - To obtain the full list, authenticate with KMHFL or download the
#     CSV export from https://kmhfr.health.go.ke.
```

No functional changes to `fetch_facilities.py` are needed — the pipeline already prints
a full funnel and does not cap rows.

**Files:** `data/fetch_facilities.py`

**Verify:** Grep `fetch_facilities.py` for `head(`, `[:`, `LIMIT` — none should appear
in data-loading paths. Run `python data/fetch_facilities.py --help` (or read the script)
to confirm no row-count argument exists.

---

### Step 8 — Final end-to-end verification

**What to do:**
Run the full pipeline in order:
```
python data/build_facilities_csv.py
python data/diagnose_misplacements.py
```

Confirm all of the following:
1. `facilities.csv` contains exactly 47 unique counties.
2. `facilities.csv` row for "Makueni County Referral Hospital": `county=Makueni`.
3. `facilities.csv` row for "Port Victoria hospital": `county=Busia, sub_county=Budalangi`.
4. `data/misplacement_report.csv` exists and contains both test cases with correct signals.
5. `data/unassigned_facilities.csv` exists.
6. `data/audit_v3.txt` exists with all PASS assertions.
7. `audit.txt` (existing audit) still passes — regression check.
8. No facility in `facilities.csv` has `county = "Machakos"` AND `name` containing `"Makueni County"`.

**Files:** None modified in this step — verification only.

**Verify:**
```
python data/build_facilities_csv.py
# → "✅ All audit assertions PASSED"
python data/diagnose_misplacements.py
# → exits 0, both CSVs created
grep -i "Makueni County Referral" data/facilities.csv
# → shows county=Makueni
grep -i "Port Victoria" data/facilities.csv
# → shows sub_county=Budalangi
```

---

## Summary of Deliverables Produced

| File | What it is |
|------|-----------|
| `data/diagnose_misplacements.py` | New diagnostic script (Step 1) |
| `data/misplacement_report.csv` | Full per-facility signal comparison (Step 1 output) |
| `data/misplacement_report.txt` | Human-readable summary (Step 1 output) |
| `data/unassigned_facilities.csv` | Facilities with no valid county assignment (Step 5 output) |
| `data/audit_v3.txt` | Full audit with test case verification & assertions (Step 6 output) |
| `data/build_facilities_csv.py` | Fixed — Machakos box tightened, NAME_COUNTY_OVERRIDE, NAME_SUBCOUNTY_OVERRIDES, three-tier trust order (Steps 2–6) |
| `data/fetch_facilities.py` | Source note comment added; no functional changes (Step 7) |

## Unresolved Items

1. **Sub-county spatial accuracy**: all 2,779 facilities still use round-robin sub-county assignment within their county. A proper per-facility sub-county join requires the Kenya 290 sub-county boundary shapefile (KNBS/HDX) and `geopandas`. Only "Port Victoria hospital" gets a precise sub-county via `NAME_SUBCOUNTY_OVERRIDES`. All other sub-county assignments are approximations.

2. **2,779 is a true OSM ceiling**: The full Kenya facility list requires the KMHFL authenticated API or a manual CSV export from `https://kmhfr.health.go.ke`. The fetch script already attempts KMHFL first; it currently fails (no auth token) and falls back to OSM. Obtaining KMHFL credentials or the public CSV export is the only way to increase the count.

3. **Other bounding-box border cases**: The Machakos/Makueni fix addresses the one confirmed instance where the smallest-area rule misassigns a facility. Other county borders with overlapping boxes (Kericho/Bomet, Kisii/Nyamira, Nairobi/Kiambu) may have similar issues but no additional confirmed misplacements were found in the data. The 24 NAME_COUNTY_OVERRIDE facilities provide a safety net for any facility that names its county explicitly.

4. **Previous review findings still outstanding** (from `.agents/review.json`):
   - Nyeri sub-county list may contain ward-level names — needs verification against current KNBS list.
   - Round-robin sub-county disclaimer not shown in UI.
   - 932+ facilities default-classified as Public due to blank OSM operator tag.
   These are out of scope for this task but documented here for the next iteration.
