# Kenya Health Facility Pipeline — County & Sub-county Data Fix

The script replaces a bounding-box + hardcoded-fallback approach with a two-stage pipeline: county assignment by smallest-area bounding-box match, then sub-county assignment by round-robin cycling through an explicit KENYA_SUB_COUNTIES dictionary. All 5 bugs from the task description are addressed. The audit shows 47/47 counties, no "Central" singleton, no Eldoret, no corrupted display names, and all audit assertions pass.

**Watch for:**
- **Round-robin sub-county assignment is not spatially accurate** (confirmed) — sub-counties are assigned by row-insertion order within each county group, not by facility coordinates. Individual facility-to-sub-county bindings are approximate.
- **Nyeri KENYA_SUB_COUNTIES contains 8 entries including "Kieni East" and "Kieni West"** (confirmed) — these are electoral ward boundaries, not administrative sub-counties. Nyeri has 6 official sub-counties; the extra two inflate the count and produce non-canonical names in the CSV.
- **Kirinyaga KENYA_SUB_COUNTIES contains "Kirinyaga East"** (confirmed) — Kirinyaga has 4 official sub-counties (Mwea, Gichugu, Ndia, Kirinyaga Central). "Kirinyaga East" does not appear in the official IEBC/KNBS administrative list.
- **"Chepalungu" appears in Kericho's sub-county list** (confirmed) — Chepalungu is a Bomet sub-county, not Kericho. Kericho's official 8 sub-counties are Ainamoi, Belgut, Bureti, Kipkelion East, Kipkelion West, Roret, Sigowet/Soin, and one of Chepalungu/Konoin depending on the source; but Chepalungu sub-county as a Kericho division is debated and more commonly attributed to Bomet.
- **Laikipia has only 1 sub-county in the CSV** (confirmed) — the audit flags this as a source-data gap (1 OSM facility), but the KENYA_SUB_COUNTIES definition is correct (3 entries). The pipeline behavior is correct; the UI will show only Laikipia West.
- **Ownership classification defaults 932 facilities to "Public"** (confirmed) — any facility with a blank or unrecognised OSM `operator` tag is classified Public. This is the correct safe default but inflates the public count materially.

**Verdict**: CHANGES_REQUESTED

---

## High-level view

All five originally reported bugs are fixed at the pipeline level. The 47-county bounding box table uses only canonical display names, Eldoret is absent, corrupted names (Taitataveta, Tanariver, Transnzoia) are gone, and CANONICAL_MAP enforces a canonical→canonical identity pass that prevents key drift. The "Central" singleton problem is fully eliminated: KENYA_SUB_COUNTIES covers all 47 counties with real official names and the fallback to "Central" has been removed.

The round-robin sub-county assignment is an acknowledged, documented approximation. It is the correct pragmatic choice given the absence of a boundary shapefile and geopandas. The limitation is disclosed in the module docstring, the audit (Sections 10–11), and the function docstring. This is not a bug but it does mean individual facility-to-sub-county bindings carry no geographic accuracy guarantee.

Three sub-county name accuracy issues exist in KENYA_SUB_COUNTIES itself. Nyeri's list contains "Kieni East" and "Kieni West", which are ward-level divisions promoted above their administrative level — Nyeri has 6 sub-counties, not 8. Kirinyaga's list contains "Kirinyaga East", which is not among the 4 official sub-counties for that county. Kericho's list contains "Chepalungu", which belongs to Bomet. These produce non-canonical sub-county names in the output CSV and cause the per-county sub-county counts in the audit to be off by one or two for these counties.

The audit report is thorough and structurally correct. All five assertions pass. The Section 10 coverage-gap table honestly exposes which defined sub-counties received no facility due to source sparsity. The ownership default-fallback count in Section 11 is a useful signal for downstream data quality work.

---

<details>
<summary>Issues (6)</summary>

1. **Nyeri sub-county list contains ward-level names** — "Kieni East" and "Kieni West" are electoral wards, not administrative sub-counties. Nyeri has 6 official sub-counties: Tetu, Kieni, Mathira, Nyeri Town, Othaya, Mukurweini. Remove the two ward entries from KENYA_SUB_COUNTIES["Nyeri"].

2. **Kirinyaga sub-county list contains a non-existent entry** — "Kirinyaga East" is not an official sub-county. The 4 official sub-counties are Mwea, Gichugu, Ndia, and Kirinyaga Central. Remove "Kirinyaga East" from KENYA_SUB_COUNTIES["Kirinyaga"].

3. **Chepalungu in Kericho sub-county list** — Chepalungu sub-county is administered under Bomet County; it appears in Kericho's KENYA_SUB_COUNTIES list in addition to Bomet's. Verify against the current KNBS/IEBC administrative boundary list and remove the incorrect entry from whichever county it doesn't belong to.

4. **Round-robin assignment produces misleading per-facility sub-county data** — the module docstring discloses this, but there is no runtime warning in the output CSV or in the clinic locator UI. Consider adding a column `sub_county_method=approximate` or a visible disclaimer in the UI so users don't trust individual facility sub-county labels. No code change is strictly required, but a UI disclaimer is strongly advisable.

5. **Laikipia will always show only Laikipia West in the clinic locator** — only 1 OSM facility exists for Laikipia, so the round-robin never cycles to Laikipia East or Laikipia North. This is a source-data gap, not a pipeline bug, but it means users from those sub-counties see no results. Acknowledged in the audit; no fix available without richer source data.

6. **932 facilities default-classified as Public** — any blank or unrecognised `operator` tag becomes "Public". The audit notes this but takes no corrective action. A mapping of common OSM operator strings to ownership categories, or a cross-reference against KMHFL ownership fields, would reduce the noise.

</details>

---

<details>
<summary>Details</summary>

### 47-county bounding box correctness

COUNTY_BOXES contains exactly 47 entries, confirmed by the `assert len(COUNTY_BOXES) == 47` guard at module load. All canonical spellings match the task's authoritative list: hyphens in Taita-Taveta, Tharaka-Nithi, Elgeyo-Marakwet; apostrophe in Murang'a; spaces in Tana River, Trans Nzoia, West Pokot, Uasin Gishu, Homa Bay. "Eldoret" is absent; the audit assertion `[PASS] 'Eldoret' does not appear as a county` confirms this at runtime.

The smallest-area tiebreaker in `assign_county` correctly handles overlapping boxes. The Nandi spot-check in the audit shows Kapsabet Hospital (lat=0.2021, lon=35.1027) assigned to Nandi rather than Uasin Gishu: Nandi's box area is ~0.18 vs Uasin Gishu's ~0.60, so the tiebreaker fires correctly.

### Sub-county dictionary accuracy

KENYA_SUB_COUNTIES covers all 47 counties (confirmed by the module-load assertion). "Central" does not appear anywhere as a sub-county value in the generated CSV — verified directly. The sub-county lists for the 20 counties originally showing only "Central" (Baringo, Busia, Elgeyo Marakwet, Embu, Isiolo, Kericho, Kirinyaga, Kitui, Kwale, Lamu, Makueni, Marsabit, Nyamira, Samburu, Siaya, Taita Taveta, Tana River, Trans Nzoia, Wajir, West Pokot) all now have real official sub-county names and multi-entry lists.

Three entries in the dictionary contain inaccurate sub-county names:

**Nyeri**: The list has 8 entries — Tetu, Kieni, Mathira, Nyeri Town, Othaya, Mukurweini, Kieni East, Kieni West. Kieni East and Kieni West are ward-level boundaries within the Kieni sub-county; they are not separate administrative sub-counties. The official Nyeri sub-county count is 6. The round-robin will cycle across 8 slots, injecting "Kieni East" and "Kieni West" as sub-county values into the CSV for ~25% of Nyeri's 17 facilities.

**Kirinyaga**: The list has 5 entries including "Kirinyaga East". The 4 official Kirinyaga sub-counties are Mwea, Gichugu, Ndia, and Kirinyaga Central. "Kirinyaga East" does not appear in the KNBS or IEBC administrative boundary lists at sub-county level.

**Kericho**: The list includes "Chepalungu". Chepalungu sub-county exists in Bomet County (it is also in Bomet's list). Whether Chepalungu appears in Kericho depends on which administrative revision is used, but the prevailing KNBS post-2013 devolution list does not include it as a Kericho sub-county.

### Round-robin sub-county assignment

`assign_sub_county` cycles through `KENYA_SUB_COUNTIES[county]` using a per-county counter incremented on each row. A county with N facilities and M defined sub-counties will have the first `N % M` sub-counties represented twice and the remaining once — or, for counties with fewer facilities than sub-counties, only the first N sub-counties appear. The audit's Section 10 table enumerates all such gaps per county. No facility receives "Unknown" unless a county key is missing from the dictionary, which the module-load assertion prevents.

The limitation this creates in the UI: users searching for Mandera South, Mandera West, Banissa, or Lafey will find zero results because OSM had only 2 Mandera facilities (Mandera East and Mandera North were assigned). Same for several Nandi, Makueni, and Laikipia sub-counties. The pipeline is not the cause — source data sparsity is — but the UI has no mechanism to communicate this to users.

### Audit report completeness

The audit covers all required checks: 47-county count, per-county sub-county/facility/ownership breakdown, unmapped rows, facilities with no coordinates, facilities with no sub-county, suspect counties, Kiambu and Uasin Gishu sub-county lists, and all five hard assertions. All five assertions pass. The Kiambu list (12 sub-counties) and Uasin Gishu list (6 sub-counties) match the official counts exactly.

Section 6 correctly identifies Laikipia (1 sub-county) as a source-data issue rather than a pipeline bug. Section 11 counts 932 ownership-default-fallback rows — roughly 52% of the 1,785 CSV rows — reflecting OSM `operator` tag sparsity, not a classification logic error.

### Output CSV structure and encoding

The CSV has exactly the 10 required columns: `name, county, sub_county, level, owner_group, lat, lon, maps_link, phone, hours`. The file is UTF-8 encoded; the em-dash in level labels (`Level 3 — Health Centre`) is stored correctly as U+2014 — PowerShell's console renders it as `â€"` due to codepage mismatch, but the file bytes are correct, verified by reading with Python's `utf-8` codec. Zero rows have `sub_county=Central` or an empty `sub_county`. No corrupted county display names appear.

### Test coverage

There are no automated tests for the pipeline. The audit script serves as a post-run integration check, but it runs only when the script is executed — there is no CI guard. The sub-county name accuracy issues (Nyeri, Kirinyaga, Kericho) would have been caught by a test that asserts each county's sub-county list against an authoritative reference fixture.

</details>

---

<details>
<summary>File map</summary>

- `data/build_facilities_csv.py` — complete rewrite: COUNTY_BOXES (47 entries), CANONICAL_MAP, KENYA_SUB_COUNTIES, assign_county (bbox+tiebreaker), assign_sub_county (round-robin), audit report generation with assertions.
- `data/audit.txt` — generated output: 47-county count, per-county breakdown, Kiambu/Uasin Gishu sub-county lists, coverage gap table, ownership default count, 5 passing assertions.
- `data/facilities.csv` — generated output: 1,785 rows, 10 columns, UTF-8, no Central sub-counties, no corrupted county names, 47 distinct counties.

Full diff: `git diff main -- data/build_facilities_csv.py data/audit.txt data/facilities.csv`

</details>
