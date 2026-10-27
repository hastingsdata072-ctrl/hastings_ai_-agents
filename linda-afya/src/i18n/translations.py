"""
Bilingual translations for the Kenya Public Health AI Assistant.
Supports English (en) and Kiswahili (sw).
"""

TRANSLATIONS = {
    "en": {
        # App general
        "app_title": "Linda Afya Health Assistant",
        "app_subtitle": "Powered by Ministry of Health Guidelines",
        "language_label": "🌐 Language / Lugha",

        # Navigation
        "nav_home": "🏠 Home",
        "nav_triage": "🩺 Symptom Checker",
        "nav_clinic": "🏥 Clinic Locator",
        "nav_immunization": "💉 Immunization Tracker",
        "nav_chat": "💬 Health Chat",

        # Home page
        "home_welcome": "Welcome to the Kenya Public Health AI Assistant",
        "home_desc": "Your AI-powered health companion aligned with Kenya Ministry of Health guidelines.",
        "home_card_triage": "Symptom Checker",
        "home_card_triage_desc": "Check your symptoms and get a triage priority (Red / Yellow / Green).",
        "home_card_clinic": "Clinic Locator",
        "home_card_clinic_desc": "Find the nearest health facility by county and service needed.",
        "home_card_immunization": "Immunization Tracker",
        "home_card_immunization_desc": "Check vaccine schedules for your child based on their age.",
        "home_card_chat": "Health Chat",
        "home_card_chat_desc": "Ask any health question and get guidance grounded in MoH protocols.",
        "home_disclaimer": "⚠️ This tool provides health guidance only. Always consult a qualified healthcare provider for medical decisions.",

        # Symptom checker
        "triage_title": "🩺 Symptom Checker",
        "triage_desc": "Enter your symptoms to receive a triage priority based on Kenya MoH guidelines.",
        "triage_symptoms_label": "What symptoms are you experiencing?",
        "triage_symptoms_placeholder": "e.g. fever, headache, cough",
        "triage_age_label": "Patient Age (years)",
        "triage_duration_label": "How many days have you had these symptoms?",
        "triage_btn": "Check Symptoms",
        "triage_result_title": "Triage Result",
        "triage_red": "🔴 RED — Emergency",
        "triage_yellow": "🟡 YELLOW — Urgent",
        "triage_green": "🟢 GREEN — Non-Urgent",
        "triage_red_msg": "EMERGENCY: Seek immediate care at the nearest Level 4+ hospital!",
        "triage_yellow_msg": "URGENT: Visit your nearest dispensary or health centre within 24 hours.",
        "triage_green_msg": "NON-URGENT: You may manage at home or visit a community health promoter.",
        "triage_action": "Recommended Action",
        "triage_error_symptoms": "Please enter at least one symptom.",

        # Clinic locator
        "clinic_title": "🏥 Clinic Locator",
        "clinic_desc": "Find the nearest health facility in your county.",
        "clinic_county_label": "Select your County",
        "clinic_service_label": "Service Needed",
        "clinic_level_label": "Minimum Facility Level",
        "clinic_btn": "Find Clinics",
        "clinic_result_title": "Nearby Facilities",
        "clinic_no_results": "No facilities found. Try broadening your criteria.",
        "clinic_name": "Facility Name",
        "clinic_ward": "Ward",
        "clinic_level": "Level",
        "clinic_hours": "Operating Hours",
        "clinic_services": "Services",

        # Immunization
        "imm_title": "💉 Immunization Tracker",
        "imm_desc": "Check your child's vaccination schedule based on the Kenya KEPI immunization program.",
        "imm_age_label": "Child's Age",
        "imm_age_unit": "Age Unit",
        "imm_age_weeks": "Weeks",
        "imm_age_months": "Months",
        "imm_age_years": "Years",
        "imm_btn": "Get Schedule",
        "imm_result_title": "Vaccination Schedule",
        "imm_vaccine": "Vaccine",
        "imm_due_age": "Due At",
        "imm_status": "Status",
        "imm_due": "✅ Due Now",
        "imm_overdue": "⚠️ Overdue",
        "imm_upcoming": "📅 Upcoming",
        "imm_done": "✔️ Should be done",
        "imm_catchup": "💊 Catch-up dose recommended — visit your nearest KEPI clinic.",

        # Chat
        "chat_title": "💬 Health Chat",
        "chat_desc": "Ask any health question. Answers are grounded in Kenya MoH guidelines.",
        "chat_placeholder": "Type your health question here...",
        "chat_btn": "Send",
        "chat_thinking": "Consulting MoH guidelines...",
        "chat_disclaimer": "This AI provides general health information only. For emergencies call 0800 720 021.",
        "chat_clear": "Clear Chat",
        "chat_you": "You",
        "chat_assistant": "Health Assistant",

        # Emergency
        "emergency_title": "🚨 EMERGENCY ALERT",
        "emergency_msg": "Based on your symptoms, you need IMMEDIATE medical attention.",
        "emergency_call": "Go to the nearest Level 4+ Hospital NOW.",
        "emergency_number": "Emergency Line: 0800 720 021",
    },

    "sw": {
        # App general
        "app_title": "Linda Afya Health Assistant",
        "app_subtitle": "Inayoendeshwa na Miongozo ya Wizara ya Afya",
        "language_label": "🌐 Language / Lugha",

        # Navigation
        "nav_home": "🏠 Nyumbani",
        "nav_triage": "🩺 Ukaguzi wa Dalili",
        "nav_clinic": "🏥 Tafuta Kliniki",
        "nav_immunization": "💉 Chanjo",
        "nav_chat": "💬 Mazungumzo ya Afya",

        # Home page
        "home_welcome": "Karibu kwa Msaidizi wa Afya ya Umma Kenya",
        "home_desc": "Msaidizi wako wa afya unaotumia AI, unaofuata miongozo ya Wizara ya Afya Kenya.",
        "home_card_triage": "Ukaguzi wa Dalili",
        "home_card_triage_desc": "Angalia dalili zako na upate kipaumbele cha matibabu (Nyekundu / Njano / Kijani).",
        "home_card_clinic": "Tafuta Kliniki",
        "home_card_clinic_desc": "Pata kituo cha afya kilicho karibu nawe kwa kaunti na huduma unayohitaji.",
        "home_card_immunization": "Chanjo",
        "home_card_immunization_desc": "Angalia ratiba ya chanjo kwa mtoto wako kulingana na umri wake.",
        "home_card_chat": "Mazungumzo ya Afya",
        "home_card_chat_desc": "Uliza swali lolote la afya na upate mwongozo kulingana na itifaki za MoH.",
        "home_disclaimer": "⚠️ Chombo hiki kinatoa mwongozo wa afya tu. Daima shauriana na mtoa huduma za afya aliyehitimu.",

        # Symptom checker
        "triage_title": "🩺 Ukaguzi wa Dalili",
        "triage_desc": "Ingiza dalili zako hapa chini kupata kipaumbele cha matibabu kulingana na miongozo ya MoH Kenya.",
        "triage_symptoms_label": "Unajisikiaje? (Dalili zako ni zipi?)",
        "triage_symptoms_placeholder": "mfano: homa, maumivu ya kichwa, kikohozi",
        "triage_age_label": "Umri wa Mgonjwa (miaka)",
        "triage_duration_label": "Umekuwa na dalili hizi kwa siku ngapi?",
        "triage_btn": "Angalia Dalili",
        "triage_result_title": "Matokeo ya Ukaguzi",
        "triage_red": "🔴 NYEKUNDU — Dharura",
        "triage_yellow": "🟡 NJANO — Haraka",
        "triage_green": "🟢 KIJANI — Si ya Haraka",
        "triage_red_msg": "DHARURA: Tafuta matibabu ya haraka katika hospitali ya karibu ya ngazi ya 4+!",
        "triage_yellow_msg": "HARAKA: Tembelea zahanati au kituo cha afya karibu nawe ndani ya masaa 24.",
        "triage_green_msg": "SI YA HARAKA: Unaweza kushughulikia nyumbani au kutembelea mkuza wa afya wa jamii.",
        "triage_action": "Hatua Inayopendekezwa",
        "triage_error_symptoms": "Tafadhali ingiza dalili angalau moja.",

        # Clinic locator
        "clinic_title": "🏥 Tafuta Kliniki",
        "clinic_desc": "Pata kituo cha afya kilicho karibu nawe katika kaunti yako.",
        "clinic_county_label": "Chagua Kaunti yako",
        "clinic_service_label": "Huduma Inayohitajika",
        "clinic_level_label": "Kiwango cha Chini cha Kituo",
        "clinic_btn": "Tafuta Vituo",
        "clinic_result_title": "Vituo vya Karibu",
        "clinic_no_results": "Hakuna vituo vilivyopatikana. Jaribu kupanua vigezo vyako.",
        "clinic_name": "Jina la Kituo",
        "clinic_ward": "Wodi",
        "clinic_level": "Ngazi",
        "clinic_hours": "Masaa ya Kufanya Kazi",
        "clinic_services": "Huduma",

        # Immunization
        "imm_title": "💉 Chanjo",
        "imm_desc": "Angalia ratiba ya chanjo ya mtoto wako kulingana na programu ya KEPI ya Kenya.",
        "imm_age_label": "Umri wa Mtoto",
        "imm_age_unit": "Kipimo cha Umri",
        "imm_age_weeks": "Wiki",
        "imm_age_months": "Miezi",
        "imm_age_years": "Miaka",
        "imm_btn": "Pata Ratiba",
        "imm_result_title": "Ratiba ya Chanjo",
        "imm_vaccine": "Chanjo",
        "imm_due_age": "Inatakiwa Umri",
        "imm_status": "Hali",
        "imm_due": "✅ Inatakiwa Sasa",
        "imm_overdue": "⚠️ Imechelewa",
        "imm_upcoming": "📅 Inakuja",
        "imm_done": "✔️ Inapaswa kuwa imefanywa",
        "imm_catchup": "💊 Dozi ya kufidia inapendekezwa — tembelea kliniki ya KEPI iliyo karibu nawe.",

        # Chat
        "chat_title": "💬 Mazungumzo ya Afya",
        "chat_desc": "Uliza swali lolote la afya. Majibu yanategemea miongozo ya MoH Kenya.",
        "chat_placeholder": "Andika swali lako la afya hapa...",
        "chat_btn": "Tuma",
        "chat_thinking": "Inashauriana na miongozo ya MoH...",
        "chat_disclaimer": "Msaidizi huyu wa AI anatoa taarifa za jumla za afya tu. Kwa dharura piga simu 0800 720 021.",
        "chat_clear": "Futa Mazungumzo",
        "chat_you": "Wewe",
        "chat_assistant": "Msaidizi wa Afya",

        # Emergency
        "emergency_title": "🚨 TAHADHARI YA DHARURA",
        "emergency_msg": "Kulingana na dalili zako, unahitaji matibabu ya HARAKA.",
        "emergency_call": "Nenda hospitali ya karibu ya ngazi ya 4+ SASA.",
        "emergency_number": "Mstari wa Dharura: 0800 720 021",
    }
}


def t(key: str, lang: str = "en") -> str:
    """Get translation for a key in the given language. Falls back to English."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )
