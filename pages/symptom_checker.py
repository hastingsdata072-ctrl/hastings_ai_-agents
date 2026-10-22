"""
Page 1: Symptom Checker
Triage form + location step → nearest appropriate health facility.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import streamlit as st

from tools.triage_engine import triage_symptoms
from i18n.translations import t

# ── Emergency numbers (Kenya, verified) ──────────────────────────────────────
EMERGENCY_NUMBERS = {
    "999":          "999 (Police / Ambulance)",
    "112":          "112 (Pan-Africa Emergency)",
    "0800 720 021": "0800 720 021 (Kenya Health — free)",
    "0800 723 253": "0800 723 253 (Red Cross — free)",
}

# ── Kenya bounding box ────────────────────────────────────────────────────────
KENYA_LAT_MIN, KENYA_LAT_MAX = -5.0,  5.5
KENYA_LON_MIN, KENYA_LON_MAX = 33.5, 42.0

# ── Minimum KEPH level per triage priority ────────────────────────────────────
MIN_LEVEL = {"RED": 4, "YELLOW": 3, "GREEN": 2}

LEVEL_ORDER = {
    "Level 2 — Dispensary":        2,
    "Level 3 — Health Centre":     3,
    "Level 4 — Hospital":          4,
    "Level 5 — County Referral":   5,
    "Level 6 — National Referral": 6,
}

RADIUS_KM = 50


# ── Helpers ───────────────────────────────────────────────────────────────────
def haversine_km(lat1, lon1, lats, lons):
    R = 6371.0
    dlat = np.radians(lats - lat1)
    dlon = np.radians(lons - lon1)
    a = (np.sin(dlat / 2) ** 2
         + np.cos(np.radians(lat1)) * np.cos(np.radians(lats))
         * np.sin(dlon / 2) ** 2)
    return R * 2 * np.arcsin(np.sqrt(a))


@st.cache_data(ttl=0)
def _load_facilities():
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "facilities.csv",
    )
    df = pd.read_csv(path)
    df["_level_num"] = df["level"].map(LEVEL_ORDER).fillna(0).astype(int)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df


def find_nearest(lat, lon, priority, owner_filter, df, top_n=5):
    min_lvl = MIN_LEVEL.get(priority, 2)
    eligible = df[df["_level_num"] >= min_lvl].copy()
    if owner_filter != "All":
        eligible = eligible[eligible["owner_group"] == owner_filter]
    has_coords = eligible.dropna(subset=["lat", "lon"])
    if has_coords.empty:
        return pd.DataFrame(), False
    dists = haversine_km(lat, lon, has_coords["lat"].values, has_coords["lon"].values)
    has_coords = has_coords.copy()
    has_coords["_dist_km"] = dists
    has_coords = has_coords.sort_values("_dist_km")
    within = has_coords[has_coords["_dist_km"] <= RADIUS_KM]
    result = within.head(top_n) if not within.empty else has_coords.head(3)
    return result, len(within) > 0


def _directions_link(plat, plon, dlat, dlon):
    if plat is not None:
        return f"https://www.google.com/maps/dir/?api=1&origin={plat},{plon}&destination={dlat},{dlon}"
    return f"https://www.google.com/maps/dir/?api=1&destination={dlat},{dlon}"


def _emergency_banner(lang):
    nums = " &nbsp;|&nbsp; ".join(
        f'<a href="tel:{k}" style="color:white;font-weight:bold">{v}</a>'
        for k, v in EMERGENCY_NUMBERS.items()
    )
    title = "DHARURA" if lang == "sw" else "EMERGENCY"
    body = (
        "Dalili zako zinaonyesha hatari ya maisha. **Usisubiri.** Nenda hospitali SASA."
        if lang == "sw" else
        "Your symptoms suggest a life-threatening condition. **Do not wait.** Go to hospital NOW."
    )
    st.markdown(
        f'<div style="background:#CC0000;color:white;padding:18px;border-radius:10px;margin-bottom:10px">'
        f'<b style="font-size:1.3rem">🚨 {title}</b><br><br>{body}<br><br>'
        f'{"Piga simu:" if lang=="sw" else "Call:"} {nums}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _facility_cards(df, pat_lat, pat_lon, lang):
    for _, row in df.iterrows():
        dist_txt = (f"{row['_dist_km']:.1f} km straight-line"
                    if "_dist_km" in row.index and pd.notna(row["_dist_km"])
                    else "")
        has_coords = pd.notna(row.get("lat")) and pd.notna(row.get("lon"))
        st.markdown(
            f'<div style="border:1px solid #ddd;border-radius:10px;'
            f'padding:14px;margin-bottom:8px;background:#fafafa">'
            f'<b>{row["name"]}</b><br>'
            f'<span style="color:#555;font-size:0.88rem">'
            f'{row.get("level","")} · {row.get("owner_group","")}'
            f'{" · " + dist_txt if dist_txt else ""}</span><br>'
            f'<span style="color:#888;font-size:0.82rem">'
            f'{row.get("sub_county","")}, {row.get("county","")}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns(2)
        with c1:
            if has_coords:
                st.link_button(
                    "📍 Directions" if lang == "en" else "📍 Maelekezo",
                    _directions_link(pat_lat, pat_lon, row["lat"], row["lon"]),
                    use_container_width=True,
                )
            else:
                st.link_button(
                    "📍 Maps" if lang == "en" else "📍 Ramani",
                    row.get("maps_link", "#"),
                    use_container_width=True,
                )
        with c2:
            ph = str(row.get("phone", ""))
            if ph not in ["", "nan"]:
                st.link_button(f"📞 {ph}", f"tel:{ph}", use_container_width=True)
        if dist_txt:
            st.caption("_Straight-line only — actual travel may be longer._"
                       if lang == "en"
                       else "_Mstari ulionyooka tu — safari halisi inaweza kuwa ndefu zaidi._")


# ═════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ═════════════════════════════════════════════════════════════════════════════
def render(lang: str = "en"):
    st.title(t("triage_title", lang))
    st.markdown(f"*{t('triage_desc', lang)}*")
    st.divider()

    # ── STEP 1: Symptom form ──────────────────────────────────────────────────
    with st.form("triage_form"):
        symptoms_input = st.text_area(
            t("triage_symptoms_label", lang),
            placeholder=t("triage_symptoms_placeholder", lang),
            height=100,
        )
        col1, col2 = st.columns(2)
        with col1:
            age = st.number_input(
                t("triage_age_label", lang),
                min_value=0.0, max_value=120.0, value=25.0, step=0.5,
                help="Decimals for infants: 0.5 = 6 months",
            )
        with col2:
            duration = st.number_input(
                t("triage_duration_label", lang),
                min_value=0, max_value=365, value=1, step=1,
            )
        submitted = st.form_submit_button(
            t("triage_btn", lang), use_container_width=True, type="primary",
        )

    # Store triage result in session so it survives reruns from radio/selectbox
    if submitted:
        if not symptoms_input.strip():
            st.error(t("triage_error_symptoms", lang))
            return
        symptoms_list = [
            s.strip()
            for s in symptoms_input.replace(",", "\n").splitlines()
            if s.strip()
        ]
        st.session_state["triage_result"] = triage_symptoms(symptoms_list, age, duration, lang)
        # Clear any old location when a new triage is run
        st.session_state.pop("pat_lat", None)
        st.session_state.pop("pat_lon", None)

    # Nothing to show until at least one triage has been run
    if "triage_result" not in st.session_state:
        return

    result   = st.session_state["triage_result"]
    priority = result["priority"]

    st.divider()

    # ── RED-FLAG BANNER — always first ────────────────────────────────────────
    if result["is_emergency"]:
        _emergency_banner(lang)

    # ── Triage priority badge ─────────────────────────────────────────────────
    st.subheader(t("triage_result_title", lang))
    bg_map = {"RED": (result["color"], "white"),
               "YELLOW": (result["color"], "#333"),
               "GREEN":  (result["color"], "white")}
    bg, fg = bg_map[priority]
    label  = {"RED": "triage_red", "YELLOW": "triage_yellow", "GREEN": "triage_green"}[priority]
    st.markdown(
        f'<div style="background:{bg};padding:16px;border-radius:10px;'
        f'color:{fg};font-size:1.4rem;font-weight:bold;text-align:center">'
        f'{t(label, lang)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

    # ── MoH protocol ─────────────────────────────────────────────────────────
    st.subheader(t("triage_action", lang))
    st.info(result["protocol"])

    if result["danger_signs_found"]:
        st.warning(f"⚠️ Danger signs: {', '.join(result['danger_signs_found'])}")
    elif result["urgent_signs_found"]:
        st.warning(f"🔔 Urgent symptoms: {', '.join(result['urgent_signs_found'])}")

    # ── STEP 2: Location ──────────────────────────────────────────────────────
    st.divider()
    st.subheader(
        "📍 Find the nearest facility"
        if lang == "en" else
        "📍 Pata kituo cha afya karibu nawe"
    )
    st.caption(
        "Your location is used only to find nearby facilities. It is not stored."
        if lang == "en" else
        "Eneo lako linatumika tu kupata vituo vya karibu. Haihifadhiwi."
    )

    df_all = _load_facilities()

    loc_method = st.radio(
        "Location method" if lang == "en" else "Njia ya eneo",
        options=[
            "Enter my coordinates" if lang == "en" else "Ingiza kuratibu zangu",
            "Select County & Sub-county" if lang == "en" else "Chagua Kaunti na Sub-kaunti",
        ],
        horizontal=True,
        key="loc_method_radio",
    )

    pat_lat = st.session_state.get("pat_lat")
    pat_lon = st.session_state.get("pat_lon")
    selected_county = None
    selected_sub    = None
    location_ready  = False

    # ── Option A: GPS coordinates ─────────────────────────────────────────────
    if "coordinates" in loc_method or "kuratibu" in loc_method:
        st.markdown(
            "Open Google Maps on your phone → long-press your spot → copy the numbers shown."
            if lang == "en" else
            "Fungua Google Maps → bonyeza mahali pako → nakili nambari zilizo juu."
        )
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            lat_val = st.text_input("Latitude", placeholder="-1.286389", key="lat_txt")
        with c2:
            lon_val = st.text_input("Longitude", placeholder="36.817223", key="lon_txt")
        with c3:
            st.markdown("<br>", unsafe_allow_html=True)
            go = st.button(
                "Go" if lang == "en" else "Tuma",
                key="go_coords", type="primary", use_container_width=True,
            )

        if go:
            try:
                lat_f = float(lat_val.strip())
                lon_f = float(lon_val.strip())
                if not (KENYA_LAT_MIN <= lat_f <= KENYA_LAT_MAX
                        and KENYA_LON_MIN <= lon_f <= KENYA_LON_MAX):
                    st.warning(
                        "Those coordinates are outside Kenya. Please check and try again."
                        if lang == "en" else
                        "Kuratibu hizo ziko nje ya Kenya. Tafadhali angalia tena."
                    )
                else:
                    st.session_state["pat_lat"] = lat_f
                    st.session_state["pat_lon"] = lon_f
                    pat_lat, pat_lon = lat_f, lon_f
                    location_ready = True
            except ValueError:
                st.error(
                    "Enter numbers only, e.g. -1.286389 and 36.817223."
                    if lang == "en" else
                    "Ingiza nambari tu, mfano -1.286389 na 36.817223."
                )
        elif pat_lat is not None:
            location_ready = True

    # ── Option B: County / Sub-county ────────────────────────────────────────
    else:
        # Clear stored coords when switching to dropdown mode
        st.session_state.pop("pat_lat", None)
        st.session_state.pop("pat_lon", None)
        pat_lat, pat_lon = None, None

        counties = sorted(df_all["county"].dropna().unique())
        selected_county = st.selectbox(
            t("clinic_county_label", lang),
            options=counties,
            index=None,
            placeholder="Choose a county..." if lang == "en" else "Chagua kaunti...",
            key="triage_county_sel",
        )
        if selected_county:
            subs = sorted(
                df_all[df_all["county"] == selected_county]["sub_county"]
                .dropna().unique()
            )
            selected_sub = st.selectbox(
                "Sub-county" if lang == "en" else "Sub-kaunti",
                options=subs,
                index=None,
                placeholder="Choose sub-county..." if lang == "en" else "Chagua sub-kaunti...",
                key="triage_sub_sel",
            )
            if selected_sub:
                location_ready = True
                # Derive approximate centroid for distance calc
                sub_facs = df_all[
                    (df_all["county"] == selected_county) &
                    (df_all["sub_county"] == selected_sub)
                ].dropna(subset=["lat", "lon"])
                if not sub_facs.empty:
                    pat_lat = sub_facs["lat"].mean()
                    pat_lon = sub_facs["lon"].mean()

    # ── Prompt if location not yet set ───────────────────────────────────────
    if not location_ready:
        st.info(
            "Select a location above to see nearby facilities."
            if lang == "en" else
            "Chagua eneo hapo juu kuona vituo vya karibu."
        )
        if result["is_emergency"]:
            st.error(
                "EMERGENCY: do not wait — go to the nearest hospital or call 999 / 112 now."
                if lang == "en" else
                "DHARURA: usisubiri — nenda hospitali ya karibu au piga simu 999 / 112 SASA."
            )
        return

    # ── STEP 3: Show nearest facilities ──────────────────────────────────────
    st.divider()
    st.subheader(
        "🏥 Nearest Health Facilities"
        if lang == "en" else
        "🏥 Vituo vya Afya Vilivyo Karibu"
    )

    owner_filter = st.radio(
        "Ownership" if lang == "en" else "Umiliki",
        ["All", "Public", "Private / Faith-based / NGO"],
        horizontal=True,
        key="owner_filter_sc",
    )
    show_more = st.checkbox(
        "Show up to 10 results" if lang == "en" else "Onyesha hadi 10",
        key="show_more_sc",
    )
    top_n = 10 if show_more else 5
    min_lvl_num = MIN_LEVEL.get(priority, 2)

    # ── With coordinates: haversine ───────────────────────────────────────────
    if pat_lat is not None and pat_lon is not None:
        nearby, any_within = find_nearest(pat_lat, pat_lon, priority, owner_filter, df_all, top_n)

        if not any_within and not nearby.empty:
            st.warning(
                f"No Level {min_lvl_num}+ facilities within {RADIUS_KM} km. "
                "Showing nearest available."
                if lang == "en" else
                f"Hakuna vituo vya Ngazi {min_lvl_num}+ ndani ya km {RADIUS_KM}. "
                "Inaonyesha karibu zaidi."
            )
            if result["is_emergency"]:
                st.error(
                    "No hospital found nearby — call 999 or 112 immediately."
                    if lang == "en" else
                    "Hakuna hospitali karibu — piga simu 999 au 112 mara moja."
                )

        if nearby.empty:
            st.error(
                "No matching facilities found. Try changing the ownership filter."
                if lang == "en" else
                "Hakuna vituo vinavyolingana. Jaribu kubadilisha kichujio."
            )
        else:
            _facility_cards(nearby, pat_lat, pat_lon, lang)

    # ── Without coordinates: county/sub-county list ───────────────────────────
    else:
        sub_df = df_all[
            (df_all["county"] == selected_county) &
            (df_all["sub_county"] == selected_sub) &
            (df_all["_level_num"] >= min_lvl_num)
        ].copy()
        if owner_filter != "All":
            sub_df = sub_df[sub_df["owner_group"] == owner_filter]

        if sub_df.empty:
            county_df = df_all[
                (df_all["county"] == selected_county) &
                (df_all["_level_num"] >= min_lvl_num)
            ].copy()
            if owner_filter != "All":
                county_df = county_df[county_df["owner_group"] == owner_filter]
            if not county_df.empty:
                st.info(
                    f"No Level {min_lvl_num}+ facilities in {selected_sub}. "
                    f"Showing {selected_county} County results."
                    if lang == "en" else
                    f"Hakuna vituo vya Ngazi {min_lvl_num}+ katika {selected_sub}. "
                    f"Inaonyesha kwa Kaunti ya {selected_county}."
                )
                sub_df = county_df

        if sub_df.empty:
            st.error(
                f"No Level {min_lvl_num}+ facilities found in {selected_county}."
                if lang == "en" else
                f"Hakuna vituo vya Ngazi {min_lvl_num}+ katika {selected_county}."
            )
        else:
            _facility_cards(sub_df.head(top_n), None, None, lang)

    # ── Disclaimer ────────────────────────────────────────────────────────────
    st.divider()
    st.caption(
        "**Disclaimer:** This tool helps you find care — it is not a medical diagnosis. "
        "If you feel unsafe or symptoms worsen, go to the nearest hospital or call **999** / **112**. "
        "Distances are straight-line; actual travel time may be longer."
        if lang == "en" else
        "**Kanusho:** Chombo hiki kinakusaidia kupata huduma — si utambuzi wa kimatibabu. "
        "Ikiwa dalili zinazidi, nenda hospitali au piga simu **999** / **112**. "
        "Umbali ni mstari ulionyooka; safari halisi inaweza kuwa ndefu zaidi."
    )

    if st.button(
        "Clear my location data" if lang == "en" else "Futa data ya eneo langu",
        key="clear_loc_sc",
    ):
        st.session_state.pop("pat_lat", None)
        st.session_state.pop("pat_lon", None)
        st.rerun()


# ── Standalone run ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    lang = st.session_state.get("lang", "en")
    render(lang)
