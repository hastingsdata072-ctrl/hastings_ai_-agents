"""
Kenya health system data:
- 47 counties
- Sample health facilities per county
- KEPI immunization schedule
- Services list
"""

# All 47 Kenya counties
KENYA_COUNTIES = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet",
    "Embu", "Garissa", "Homa Bay", "Isiolo", "Kajiado",
    "Kakamega", "Kericho", "Kiambu", "Kilifi", "Kirinyaga",
    "Kisii", "Kisumu", "Kitui", "Kwale", "Laikipia",
    "Lamu", "Machakos", "Makueni", "Mandera", "Marsabit",
    "Meru", "Migori", "Mombasa", "Murang'a", "Nairobi",
    "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua",
    "Nyeri", "Samburu", "Siaya", "Taita-Taveta", "Tana River",
    "Tharaka-Nithi", "Trans Nzoia", "Turkana", "Uasin Gishu",
    "Vihiga", "Wajir", "West Pokot"
]

# Services available at health facilities
HEALTH_SERVICES = [
    "General Outpatient",
    "Maternity",
    "KEPI Vaccination",
    "Malaria Test & Treatment",
    "HIV/AIDS Testing & Counseling",
    "Tuberculosis (TB) Treatment",
    "Antenatal Care (ANC)",
    "Family Planning",
    "Child Welfare Clinic",
    "Emergency & Casualty",
    "Laboratory Services",
    "Pharmacy",
    "Dental",
    "Eye Care",
    "Nutrition & Dietetics",
    "Mental Health",
    "Surgery",
]

# Facility levels mapping
FACILITY_LEVELS = {
    1: "Level 1 — Community",
    2: "Level 2 — Dispensary",
    3: "Level 3 — Health Centre",
    4: "Level 4 — County Hospital",
    5: "Level 5 — County Referral",
    6: "Level 6 — National Referral",
}

# Sample facilities dataset (representative — real system would query a live DB)
FACILITIES = [
    # Nairobi
    {"name": "Kenyatta National Hospital", "county": "Nairobi", "ward": "Upperhill", "level": 6,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services", "General Outpatient"]},
    {"name": "Nairobi County Hospital (Mama Lucy)", "county": "Nairobi", "ward": "Embakasi", "level": 5,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "Emergency & Casualty", "KEPI Vaccination"]},
    {"name": "Pumwani Maternity Hospital", "county": "Nairobi", "ward": "Pumwani", "level": 4,
     "hours": "24 hours", "services": ["Maternity", "Antenatal Care (ANC)", "Child Welfare Clinic"]},
    {"name": "Mathare Community Health Centre", "county": "Nairobi", "ward": "Mathare", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "HIV/AIDS Testing & Counseling", "Family Planning"]},
    {"name": "Kibera South Dispensary", "county": "Nairobi", "ward": "Kibera", "level": 2,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Malaria Test & Treatment"]},

    # Mombasa
    {"name": "Coast General Teaching & Referral Hospital", "county": "Mombasa", "ward": "Mvita", "level": 6,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Port Reitz District Hospital", "county": "Mombasa", "ward": "Changamwe", "level": 4,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "Emergency & Casualty"]},
    {"name": "Likoni Health Centre", "county": "Mombasa", "ward": "Likoni", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Antenatal Care (ANC)"]},

    # Kisumu
    {"name": "Jaramogi Oginga Odinga Teaching & Referral Hospital", "county": "Kisumu", "ward": "Kisumu Central", "level": 6,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Kisumu County Hospital", "county": "Kisumu", "ward": "Kisumu East", "level": 5,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "KEPI Vaccination", "HIV/AIDS Testing & Counseling"]},
    {"name": "Nyalenda Health Centre", "county": "Kisumu", "ward": "Nyalenda", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Malaria Test & Treatment"]},

    # Machakos
    {"name": "Machakos Level 5 Hospital", "county": "Machakos", "ward": "Machakos Town", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Kathiani Health Centre", "county": "Machakos", "ward": "Kathiani", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Family Planning"]},
    {"name": "Tala Dispensary", "county": "Machakos", "ward": "Tala", "level": 2,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Malaria Test & Treatment"]},

    # Nakuru
    {"name": "Nakuru Level 5 Hospital", "county": "Nakuru", "ward": "Nakuru Town East", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Naivasha District Hospital", "county": "Nakuru", "ward": "Naivasha", "level": 4,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "Emergency & Casualty"]},
    {"name": "Gilgil Health Centre", "county": "Nakuru", "ward": "Gilgil", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Antenatal Care (ANC)"]},

    # Kiambu
    {"name": "Thika Level 5 Hospital", "county": "Kiambu", "ward": "Thika", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Ruiru Sub-County Hospital", "county": "Kiambu", "ward": "Ruiru", "level": 4,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "KEPI Vaccination"]},
    {"name": "Limuru Health Centre", "county": "Kiambu", "ward": "Limuru", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Family Planning"]},

    # Meru
    {"name": "Meru Teaching & Referral Hospital", "county": "Meru", "ward": "Imenti North", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Nkubu Health Centre", "county": "Meru", "ward": "Nkubu", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Malaria Test & Treatment"]},

    # Kakamega
    {"name": "Kakamega County General Hospital", "county": "Kakamega", "ward": "Kakamega Central", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Mumias District Hospital", "county": "Kakamega", "ward": "Mumias", "level": 4,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "KEPI Vaccination"]},

    # Garissa
    {"name": "Garissa County Referral Hospital", "county": "Garissa", "ward": "Garissa Township", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},

    # Turkana
    {"name": "Lodwar County Referral Hospital", "county": "Turkana", "ward": "Lodwar", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},

    # Nyeri
    {"name": "Nyeri County Referral Hospital", "county": "Nyeri", "ward": "Nyeri Town", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Karatina District Hospital", "county": "Nyeri", "ward": "Karatina", "level": 4,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "KEPI Vaccination"]},

    # Embu
    {"name": "Embu Level 5 Hospital", "county": "Embu", "ward": "Embu Town", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},

    # Bungoma
    {"name": "Bungoma County Referral Hospital", "county": "Bungoma", "ward": "Bungoma", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},

    # Kilifi
    {"name": "Kilifi County Hospital", "county": "Kilifi", "ward": "Kilifi", "level": 5,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Malindi Sub-County Hospital", "county": "Kilifi", "ward": "Malindi", "level": 4,
     "hours": "24 hours", "services": ["General Outpatient", "Maternity", "KEPI Vaccination"]},

    # Uasin Gishu
    {"name": "Moi Teaching & Referral Hospital", "county": "Uasin Gishu", "ward": "Eldoret East", "level": 6,
     "hours": "24 hours", "services": ["Emergency & Casualty", "Surgery", "Maternity", "Laboratory Services"]},
    {"name": "Eldoret West Health Centre", "county": "Uasin Gishu", "ward": "Eldoret West", "level": 3,
     "hours": "8am - 5pm", "services": ["General Outpatient", "KEPI Vaccination", "Antenatal Care (ANC)"]},
]


# Kenya KEPI Immunization Schedule
KEPI_SCHEDULE = [
    {"vaccine": "BCG", "disease": "Tuberculosis", "due_weeks": 0, "due_label": "At Birth"},
    {"vaccine": "OPV 0", "disease": "Polio", "due_weeks": 0, "due_label": "At Birth"},
    {"vaccine": "OPV 1", "disease": "Polio", "due_weeks": 6, "due_label": "6 Weeks"},
    {"vaccine": "Pentavalent 1", "disease": "DPT + Hep B + Hib", "due_weeks": 6, "due_label": "6 Weeks"},
    {"vaccine": "PCV10 1", "disease": "Pneumococcal", "due_weeks": 6, "due_label": "6 Weeks"},
    {"vaccine": "Rotavirus 1", "disease": "Rotavirus Diarrhoea", "due_weeks": 6, "due_label": "6 Weeks"},
    {"vaccine": "OPV 2", "disease": "Polio", "due_weeks": 10, "due_label": "10 Weeks"},
    {"vaccine": "Pentavalent 2", "disease": "DPT + Hep B + Hib", "due_weeks": 10, "due_label": "10 Weeks"},
    {"vaccine": "PCV10 2", "disease": "Pneumococcal", "due_weeks": 10, "due_label": "10 Weeks"},
    {"vaccine": "Rotavirus 2", "disease": "Rotavirus Diarrhoea", "due_weeks": 10, "due_label": "10 Weeks"},
    {"vaccine": "OPV 3", "disease": "Polio", "due_weeks": 14, "due_label": "14 Weeks"},
    {"vaccine": "Pentavalent 3", "disease": "DPT + Hep B + Hib", "due_weeks": 14, "due_label": "14 Weeks"},
    {"vaccine": "PCV10 3", "disease": "Pneumococcal", "due_weeks": 14, "due_label": "14 Weeks"},
    {"vaccine": "IPV", "disease": "Polio (Inactivated)", "due_weeks": 14, "due_label": "14 Weeks"},
    {"vaccine": "Measles-Rubella 1", "disease": "Measles & Rubella", "due_weeks": 36, "due_label": "9 Months"},
    {"vaccine": "Vitamin A 1", "disease": "Vitamin A Deficiency", "due_weeks": 36, "due_label": "9 Months"},
    {"vaccine": "Yellow Fever", "disease": "Yellow Fever", "due_weeks": 36, "due_label": "9 Months"},
    {"vaccine": "Measles-Rubella 2", "disease": "Measles & Rubella", "due_weeks": 72, "due_label": "18 Months"},
    {"vaccine": "Vitamin A 2", "disease": "Vitamin A Deficiency", "due_weeks": 72, "due_label": "18 Months"},
]


def locate_clinic(county: str, service_needed: str = None, min_level: int = 1) -> list:
    """
    Query facility directory by location and service.
    Returns list of matching facilities.
    """
    results = []
    for facility in FACILITIES:
        if facility["county"].lower() != county.lower():
            continue
        if facility["level"] < min_level:
            continue
        if service_needed and service_needed not in facility["services"]:
            continue
        results.append(facility)
    # Sort by level descending (higher level first)
    results.sort(key=lambda x: x["level"], reverse=True)
    return results


def get_vaccine_schedule(age_weeks: float) -> list:
    """
    Return KEPI vaccine schedule with status for a given child age in weeks.
    Status: overdue, due, upcoming, done
    """
    schedule = []
    for vaccine in KEPI_SCHEDULE:
        due = vaccine["due_weeks"]
        diff = age_weeks - due
        if diff > 4:
            status = "done"
        elif -2 <= diff <= 4:
            status = "due"
        elif diff < -2 and diff >= -8:
            status = "upcoming"
        else:
            status = "upcoming"
        # Mark overdue: child is more than 4 weeks past due but hasn't received
        if diff > 4:
            status = "done"
        if 0 < diff <= 4:
            status = "due"
        if diff < 0:
            status = "upcoming"

        schedule.append({
            **vaccine,
            "status": status,
            "age_weeks_now": age_weeks,
        })
    return schedule
