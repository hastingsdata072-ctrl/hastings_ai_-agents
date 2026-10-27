"""
Triage Engine — evaluates symptoms against Kenya MoH decision matrix.
Returns Red / Yellow / Green priority + recommended action.
This is used both as a standalone tool and by the LangChain agent.
"""

from typing import List, Dict

# ── Red flag symptoms (immediate emergency) ──────────────────────────────────
RED_FLAG_SYMPTOMS = [
    "convulsion", "convulsions", "seizure", "seizures",
    "unconscious", "unresponsive", "not breathing", "difficulty breathing",
    "severe respiratory distress", "respiratory distress",
    "chest pain", "severe chest pain",
    "coughing blood", "blood in stool", "bloody stool",
    "severe bleeding", "heavy bleeding",
    "severe dehydration", "sunken eyes", "not drinking",
    "stiff neck", "neck stiffness",
    "high fever with rash", "purple rash",
    "lethargy", "lethargic", "very weak", "cannot stand",
    "poisoning", "snake bite", "snakebite",
    "severe burns", "trauma",
    "stroke", "paralysis",
    "severe abdominal pain",
    "severe headache",
]

# ── Yellow flag symptoms (urgent — see a clinician within 24h) ─────────────
YELLOW_FLAG_SYMPTOMS = [
    "fever", "high temperature", "homa",
    "persistent cough", "cough", "kikohozi",
    "diarrhea", "vomiting", "nausea",
    "abdominal pain", "stomach ache", "stomach pain",
    "difficulty swallowing", "sore throat",
    "ear pain", "earache",
    "painful urination", "urinary problems",
    "skin rash", "rash",
    "eye discharge", "red eyes",
    "fast breathing",
    "not eating", "poor feeding",
    "swollen lymph nodes",
    "weight loss",
    "night sweats",
    "joint pain", "muscle pain",
    "headache", "maumivu ya kichwa",
]

# ── MoH action protocols per priority ─────────────────────────────────────────
MOH_PROTOCOLS = {
    "RED": {
        "en": (
            "EMERGENCY — Danger signs detected.\n"
            "• Immediately go to the nearest Level 4+ hospital or call emergency services.\n"
            "• Do NOT wait or attempt home treatment.\n"
            "• Emergency line: 0800 720 021"
        ),
        "sw": (
            "DHARURA — Dalili za hatari zimegunduliwa.\n"
            "• Nenda mara moja hospitali ya karibu ya ngazi ya 4+ au piga simu huduma za dharura.\n"
            "• USISUBIRI au kujaribu matibabu ya nyumbani.\n"
            "• Mstari wa dharura: 0800 720 021"
        ),
    },
    "YELLOW": {
        "en": (
            "URGENT CARE REQUIRED.\n"
            "• Visit your nearest dispensary (Level 2) or health centre (Level 3) within 24 hours.\n"
            "• Inform the health worker of all symptoms and their duration.\n"
            "• Keep the patient hydrated and rested.\n"
            "• If symptoms worsen, treat as RED."
        ),
        "sw": (
            "HUDUMA YA HARAKA INAHITAJIKA.\n"
            "• Tembelea zahanati (Ngazi ya 2) au kituo cha afya (Ngazi ya 3) karibu nawe ndani ya masaa 24.\n"
            "• Mwambie mhudumu wa afya dalili zote na muda wake.\n"
            "• Mgonjwa anywe maji mengi na apumzike.\n"
            "• Dalili zikiwa mbaya zaidi, zishughulikie kama NYEKUNDU."
        ),
    },
    "GREEN": {
        "en": (
            "HOME MANAGEMENT APPROPRIATE.\n"
            "• You may manage symptoms at home with rest and oral rehydration.\n"
            "• Contact your Community Health Promoter (CHP) for guidance.\n"
            "• Visit a dispensary if symptoms persist beyond 3 days or worsen.\n"
            "• Ensure adequate hydration and nutrition."
        ),
        "sw": (
            "USIMAMIZI WA NYUMBANI UNAFAA.\n"
            "• Unaweza kushughulikia dalili nyumbani kwa kupumzika na kunywa maji ya ORS.\n"
            "• Wasiliana na Mkuza wa Afya wa Jamii (CHP) kwa mwongozo.\n"
            "• Tembelea zahanati dalili zikiendelea zaidi ya siku 3 au kuzidi.\n"
            "• Hakikisha unanywa maji ya kutosha na kula vizuri."
        ),
    },
}


def triage_symptoms(
    symptoms: List[str],
    age_years: float,
    duration_days: int,
    lang: str = "en",
) -> Dict:
    """
    Evaluate symptoms against MoH decision matrix.

    Parameters:
        symptoms    : list of symptom strings reported by the patient
        age_years   : patient age in years (use decimals for months, e.g. 0.5 for 6 months)
        duration_days: how many days symptoms have been present
        lang        : language code 'en' or 'sw'

    Returns:
        dict with keys: priority, color, protocol, danger_signs_found, is_emergency
    """
    symptoms_lower = [s.lower().strip() for s in symptoms]
    combined = " ".join(symptoms_lower)

    danger_signs_found = []
    urgent_signs_found = []

    # Check red flags
    for flag in RED_FLAG_SYMPTOMS:
        if flag in combined:
            danger_signs_found.append(flag)

    # Check yellow flags
    for flag in YELLOW_FLAG_SYMPTOMS:
        if flag in combined:
            urgent_signs_found.append(flag)

    # Under-5 rule: lethargy or not eating in children under 5 → RED
    if age_years < 5:
        under5_red = ["lethargy", "lethargic", "not eating", "poor feeding",
                      "not drinking", "fast breathing", "very weak"]
        for flag in under5_red:
            if flag in combined and flag not in danger_signs_found:
                danger_signs_found.append(f"{flag} (under-5 danger sign)")

    # Long duration escalation: yellow symptoms lasting > 7 days → escalate
    if duration_days > 7 and urgent_signs_found and not danger_signs_found:
        danger_signs_found.append(f"symptoms persisting > 7 days")

    # Determine priority
    if danger_signs_found:
        priority = "RED"
        color = "#FF4444"
    elif urgent_signs_found:
        priority = "YELLOW"
        color = "#FFB300"
    else:
        priority = "GREEN"
        color = "#00C853"

    protocol = MOH_PROTOCOLS[priority][lang]

    return {
        "priority": priority,
        "color": color,
        "protocol": protocol,
        "danger_signs_found": danger_signs_found,
        "urgent_signs_found": urgent_signs_found,
        "is_emergency": priority == "RED",
        "age_years": age_years,
        "duration_days": duration_days,
    }
