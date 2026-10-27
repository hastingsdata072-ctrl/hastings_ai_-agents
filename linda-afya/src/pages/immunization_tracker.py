"""
Page 3: Immunization Tracker
KEPI vaccine schedule based on child's age.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
from data.kenya_data import get_vaccine_schedule
from i18n.translations import t


def render(lang: str = "en"):
    st.title(t("imm_title", lang))
    st.markdown(f"*{t('imm_desc', lang)}*")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        age_value = st.number_input(
            t("imm_age_label", lang),
            min_value=0,
            max_value=200,
            value=6,
            step=1,
        )
    with col2:
        age_unit = st.selectbox(
            t("imm_age_unit", lang),
            options=[
                t("imm_age_weeks", lang),
                t("imm_age_months", lang),
                t("imm_age_years", lang),
            ],
        )

    get_schedule = st.button(
        t("imm_btn", lang),
        type="primary",
        use_container_width=True,
    )

    if get_schedule:
        # Convert to weeks
        unit_en = age_unit.lower()
        if "week" in unit_en or "wiki" in unit_en:
            age_weeks = float(age_value)
        elif "month" in unit_en or "miezi" in unit_en:
            age_weeks = float(age_value) * 4.33
        else:  # years / miaka
            age_weeks = float(age_value) * 52.18

        schedule = get_vaccine_schedule(age_weeks)

        st.divider()
        st.subheader(t("imm_result_title", lang))

        # ── Summary stats ─────────────────────────────────────────────────────
        due_now   = [v for v in schedule if v["status"] == "due"]
        overdue   = [v for v in schedule if v["status"] == "overdue"]
        upcoming  = [v for v in schedule if v["status"] == "upcoming"]
        done      = [v for v in schedule if v["status"] == "done"]

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric("✅ Due Now",  len(due_now))
        col_b.metric("⚠️ Overdue",  len(overdue))
        col_c.metric("📅 Upcoming", len(upcoming))
        col_d.metric("✔️ Done",     len(done))

        if overdue:
            st.warning(t("imm_catchup", lang))

        # ── Vaccine table ─────────────────────────────────────────────────────
        st.markdown("---")

        status_labels = {
            "due":      t("imm_due", lang),
            "overdue":  t("imm_overdue", lang),
            "upcoming": t("imm_upcoming", lang),
            "done":     t("imm_done", lang),
        }

        rows = []
        for v in schedule:
            rows.append({
                t("imm_vaccine", lang): v["vaccine"],
                "Disease / Ugonjwa":    v["disease"],
                t("imm_due_age", lang): v["due_label"],
                t("imm_status", lang):  status_labels.get(v["status"], v["status"]),
            })

        df = pd.DataFrame(rows)

        # Colour rows by status
        def colour_status(row):
            s = row[t("imm_status", lang)]
            if "Due Now" in s or "Inatakiwa Sasa" in s:
                return ["background-color: #e8f5e9"] * len(row)
            elif "Overdue" in s or "Imechelewa" in s:
                return ["background-color: #fff3e0"] * len(row)
            elif "Upcoming" in s or "Inakuja" in s:
                return ["background-color: #e3f2fd"] * len(row)
            else:
                return ["background-color: #f5f5f5"] * len(row)

        styled_df = df.style.apply(colour_status, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

        st.caption(
            "Source: Kenya National Immunization Schedule (KEPI) | Ministry of Health"
            if lang == "en"
            else "Chanzo: Ratiba ya Kitaifa ya Chanjo ya Kenya (KEPI) | Wizara ya Afya"
        )


# ── Run standalone ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    lang = st.session_state.get("lang", "en")
    render(lang)
