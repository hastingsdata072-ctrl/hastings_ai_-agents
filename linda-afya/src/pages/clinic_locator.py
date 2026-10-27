"""
Page 2: Clinic Locator
County → Sub-county → Facilities with Google Maps links.
Logic adapted from files.zip (app.py + build_data.py).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Fullscreen
from streamlit.components.v1 import html as st_html
from urllib.parse import quote_plus

from i18n.translations import t

# ── Data path ─────────────────────────────────────────────────────────────────
DATA_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CSV_PATH  = os.path.join(DATA_DIR, "facilities.csv")
MAP_PATH  = os.path.join(DATA_DIR, "kenya_hospitals_map.html")


@st.cache_data(ttl=0)
def load_facilities() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    for col in ["name", "county", "sub_county", "level", "owner_group", "hours", "phone"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    return df


def build_map(df_sub: pd.DataFrame) -> folium.Map:
    """Build a folium map for a filtered set of facilities."""
    center_lat = df_sub["lat"].dropna().mean()
    center_lon = df_sub["lon"].dropna().mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")
    Fullscreen().add_to(m)
    cluster = MarkerCluster(options={"maxClusterRadius": 40}).add_to(m)

    color_map = {
        "Level 4 — Hospital":           "red",
        "Level 5 — County Referral":    "darkred",
        "Level 6 — National Referral":  "black",
        "Level 3 — Health Centre":      "blue",
        "Level 2 — Dispensary":         "green",
    }

    for _, row in df_sub.iterrows():
        try:
            lat, lon = float(row["lat"]), float(row["lon"])
        except (ValueError, TypeError):
            continue

        color   = color_map.get(row.get("level", ""), "gray")
        phone   = row.get("phone", "")
        hours   = row.get("hours", "")
        popup   = f"""
        <div style="font-family:Arial;min-width:180px">
            <b style="color:#006633">{row['name']}</b><br>
            <b>Level:</b> {row.get('level','')}<br>
            <b>Ownership:</b> {row.get('owner_group','')}<br>
            {'<b>Hours:</b> ' + hours + '<br>' if hours and hours != 'Contact facility' else ''}
            {'📞 ' + phone + '<br>' if phone else ''}
            <a href="{row.get('maps_link','')}" target="_blank">📍 Google Maps</a>
        </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(popup, max_width=260),
            tooltip=row["name"],
            icon=folium.Icon(color=color, icon="plus-sign", prefix="glyphicon"),
        ).add_to(cluster)

    return m


def render(lang: str = "en"):
    st.title(t("clinic_title", lang))
    st.markdown(f"*{t('clinic_desc', lang)}*")
    st.divider()

    # ── Load data ─────────────────────────────────────────────────────────────
    try:
        data = load_facilities()
    except FileNotFoundError:
        st.error("facilities.csv not found. Run `python data/build_facilities_csv.py` first.")
        return

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs([
        "🔍 Search Facilities" if lang == "en" else "🔍 Tafuta Vituo",
        "🗺️ Full Kenya Map"    if lang == "en" else "🗺️ Ramani ya Kenya Yote",
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — Search: County → Sub-county → Facilities
    # ════════════════════════════════════════════════════════════════════════
    with tab1:

        # 1. County
        counties = sorted(data["county"].unique())
        county = st.selectbox(
            t("clinic_county_label", lang),
            options=counties,
            index=None,
            placeholder="Choose a county..." if lang == "en" else "Chagua kaunti...",
        )

        if county:
            in_county = data[data["county"] == county]

            # 2. Sub-county
            sub_counties = sorted(in_county["sub_county"].unique())
            sub_county = st.selectbox(
                "Select your Sub-county" if lang == "en" else "Chagua Sub-kaunti yako",
                options=sub_counties,
                index=None,
                placeholder="Choose a sub-county..." if lang == "en" else "Chagua sub-kaunti...",
            )

            if sub_county:
                local = in_county[in_county["sub_county"] == sub_county].copy()

                # 3. Ownership filter
                owner = st.radio(
                    "Ownership" if lang == "en" else "Umiliki",
                    ["All / Yote", "Public", "Private / Faith-based / NGO"],
                    horizontal=True,
                )
                if not owner.startswith("All"):
                    local = local[local["owner_group"] == owner]

                st.divider()
                st.subheader(
                    f"**{len(local)}** facilit{'y' if len(local)==1 else 'ies'} in {sub_county}, {county}"
                    if lang == "en"
                    else f"Vituo **{len(local)}** katika {sub_county}, {county}"
                )

                if local.empty:
                    st.info(
                        "No facilities match this filter. Try selecting 'All' for ownership."
                        if lang == "en"
                        else "Hakuna vituo vinavyolingana. Jaribu kuchagua 'Yote' kwa umiliki."
                    )
                else:
                    # ── Map ───────────────────────────────────────────────────
                    df_map = local.dropna(subset=["lat","lon"])
                    if not df_map.empty:
                        m = build_map(df_map)
                        st_html(m._repr_html_(), height=420)
                        st.markdown("")

                    # ── Table with Google Maps links ───────────────────────────
                    st.dataframe(
                        local[["name", "level", "owner_group", "maps_link"]].rename(columns={
                            "name":        "Facility" if lang=="en" else "Kituo",
                            "level":       "Type / Level" if lang=="en" else "Aina / Ngazi",
                            "owner_group": "Ownership" if lang=="en" else "Umiliki",
                            "maps_link":   "Google Maps",
                        }),
                        column_config={
                            "Google Maps": st.column_config.LinkColumn(
                                "Google Maps",
                                display_text="📍 Open map" if lang=="en" else "📍 Fungua ramani",
                            ),
                        },
                        hide_index=True,
                        use_container_width=True,
                    )

                    # ── Pick a single facility ─────────────────────────────────
                    st.markdown("---")
                    choice = st.selectbox(
                        "Select a specific facility for details"
                        if lang == "en" else "Chagua kituo kimoja kwa maelezo",
                        options=[""] + list(local["name"]),
                        index=0,
                    )
                    if choice:
                        row = local[local["name"] == choice].iloc[0]
                        st.success(f"**{row['name']}** — {row.get('level','')} ({row.get('owner_group','')})")

                        c1, c2 = st.columns(2)
                        with c1:
                            if row.get("hours") and row["hours"] not in ["", "Contact facility"]:
                                st.markdown(f"🕐 **Hours:** {row['hours']}")
                            if row.get("phone") and row["phone"] != "":
                                st.markdown(f"📞 **Phone:** {row['phone']}")
                        with c2:
                            st.link_button(
                                "📍 Open in Google Maps",
                                row["maps_link"],
                                use_container_width=True,
                            )

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — Full Kenya Map
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown(
            f"### 🗺️ All {len(data):,} Health Facilities Across Kenya"
            if lang == "en"
            else f"### 🗺️ Vituo vyote {len(data):,} vya Afya nchini Kenya"
        )
        st.caption(
            "Click any marker for facility details. Zoom in to see individual facilities."
            if lang == "en"
            else "Bonyeza alama yoyote kwa maelezo. Kuza ili kuona vituo binafsi."
        )

        if os.path.exists(MAP_PATH):
            with open(MAP_PATH, "r", encoding="utf-8") as f:
                map_html = f.read()
            st_html(map_html, height=580)
        else:
            st.info("Generating map...")
            df_valid = data.dropna(subset=["lat","lon"])
            m = build_map(df_valid.head(500))
            st_html(m._repr_html_(), height=580)

        # Stats row
        st.divider()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Facilities" if lang=="en" else "Vituo Vyote", f"{len(data):,}")
        c2.metric("Counties"         if lang=="en" else "Kaunti",      data["county"].nunique())
        c3.metric("Public"           if lang=="en" else "Ya Serikali",
                  len(data[data["owner_group"]=="Public"]))
        c4.metric("Private/NGO"      if lang=="en" else "Binafsi/NGO",
                  len(data[data["owner_group"]=="Private / Faith-based / NGO"]))
