"""
AI client for Linda Afya Health Assistant.
Uses OpenRouter API (OpenAI-compatible) with DeepSeek V3 as the primary model.
Falls back gracefully to a mock response if the API is unavailable.

Note: Will be migrated to Amazon Bedrock AgentCore for deployment.
"""

import os
import requests

try:
    import streamlit as st
    _st_available = True
except ImportError:
    _st_available = False

# ── Configuration ─────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = (
    st.secrets.get("OPENROUTER_API_KEY")
    if _st_available and hasattr(st, "secrets")
    else None
) or os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_URL     = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID           = "nvidia/nemotron-3-ultra-550b-a55b:free"
SITE_URL           = "https://linda-afya.health"
SITE_NAME          = "Linda Afya Health Assistant"
CA_BUNDLE          = r"C:\Users\user\.aws\ca-bundle.crt"

# ── System prompt grounded in Kenya MoH guidelines ────────────────────────────
SYSTEM_PROMPT = """You are Linda Afya Health Assistant, an AI health companion aligned with the Kenya Ministry of Health (MoH) guidelines.

NOTE: You are not an official Ministry of Health application. Users should exercise caution and always consult a qualified healthcare provider for medical decisions.

Your knowledge is grounded in:
1. Kenya Community Clinical Guidelines Vol. I & II (Levels 1–3)
2. Kenya National Immunization Schedule (KEPI)
3. Kenya KPHEOC Public Health Emergency Operations Guidelines
4. Primary Health Care (PHC) Network guidelines

Your responsibilities:
- Provide accurate, evidence-based health guidance aligned with Kenya MoH protocols
- Recommend the appropriate facility level (Level 1–6) for the user's condition
- Guide users on preventive care, immunization schedules, and healthy practices
- Always recommend professional medical consultation for serious conditions
- Be culturally sensitive to the Kenyan context

Safety rules (NEVER break these):
- If a user describes danger signs (convulsions, severe breathing difficulty, unconsciousness, severe bleeding),
  IMMEDIATELY advise them to go to the nearest Level 4+ hospital or call 0800 720 021
- Never provide specific drug dosages — always refer to a healthcare provider
- Never diagnose — provide guidance and triage only
- Always end responses with a reminder to consult a qualified health provider

Respond in the same language the user writes in (English or Kiswahili).
Keep responses concise, clear, and actionable."""


def ask_health_assistant(
    user_message: str,
    chat_history: list = None,
    lang: str = "en",
) -> str:
    """
    Send a message to the AI via OpenRouter and return the response.
    Falls back to a keyword-based mock response if the API is unavailable.

    Parameters:
        user_message : the user's health question
        chat_history : list of previous {"role": "user"/"assistant", "content": "..."} dicts
        lang         : 'en' or 'sw'

    Returns:
        str response from the AI
    """
    # Build messages array
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat_history:
        for msg in chat_history[-6:]:  # keep last 6 turns for context
            messages.append({
                "role": msg["role"],
                "content": msg["content"],
            })
    messages.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME,
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_ID,
                "messages": messages,
                "max_tokens": 1024,
                "temperature": 0.3,
            },
            timeout=30,
            verify=CA_BUNDLE if os.path.exists(CA_BUNDLE) else True,
        )

        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"]
        else:
            # API error — fall back to mock
            return _mock_response(user_message, lang)

    except Exception:
        return _mock_response(user_message, lang)


def _mock_response(user_message: str, lang: str = "en") -> str:
    """
    Fallback response when the API is unavailable.
    Provides keyword-based health guidance aligned with Kenya MoH protocols.
    """
    msg_lower = user_message.lower()

    # Emergency keywords
    emergency_keywords = ["convulsion", "seizure", "unconscious", "not breathing",
                          "severe bleeding", "stroke", "chest pain"]
    if any(kw in msg_lower for kw in emergency_keywords):
        if lang == "sw":
            return (
                "🚨 **DHARURA YA KIMATIBABU**\n\n"
                "Dalili unazozielezea ni hatari sana. **Nenda mara moja hospitali ya karibu ya ngazi ya 4+ au piga simu 0800 720 021.**\n\n"
                "Usisubiri — tafuta msaada wa haraka sasa hivi."
            )
        return (
            "🚨 **MEDICAL EMERGENCY**\n\n"
            "The symptoms you describe are serious danger signs. "
            "**Go immediately to the nearest Level 4+ hospital or call 0800 720 021.**\n\n"
            "Do not wait — seek help right now."
        )

    # Malaria keywords
    if any(kw in msg_lower for kw in ["malaria", "fever", "homa", "chills"]):
        if lang == "sw":
            return (
                "**Malaria na Homa — Mwongozo wa MoH Kenya**\n\n"
                "Malaria ni ugonjwa wa kawaida nchini Kenya, hasa katika maeneo ya pwani na ziwa Victoria.\n\n"
                "**Dalili za malaria ni pamoja na:**\n"
                "- Homa kali, baridi, maumivu ya mwili\n"
                "- Maumivu ya kichwa na kuchoka\n\n"
                "**Hatua za kuchukua:**\n"
                "1. Nenda zahanati au kituo cha afya karibu nawe kufanya kipimo cha RDT (haraka)\n"
                "2. Epuka kujidozisha dawa bila ushauri wa daktari\n"
                "3. Lala chini ya neti iliyotibiwa (LLIN)\n\n"
                "⚠️ Homa kali kwa mtoto chini ya miaka 5 ni dharura — nenda hospitali mara moja."
            )
        return (
            "**Malaria & Fever — Kenya MoH Guidance**\n\n"
            "Malaria is common in Kenya, especially in coastal and Lake Victoria regions.\n\n"
            "**Typical malaria symptoms include:**\n"
            "- High fever, chills, body aches\n"
            "- Headache and fatigue\n\n"
            "**Recommended steps:**\n"
            "1. Visit your nearest dispensary or health centre for a rapid RDT test\n"
            "2. Do not self-medicate with antimalarials without confirmation\n"
            "3. Sleep under a treated bed net (LLIN)\n\n"
            "⚠️ High fever in a child under 5 is an emergency — go to hospital immediately."
        )

    # Vaccination keywords
    if any(kw in msg_lower for kw in ["vaccine", "vaccination", "chanjo", "kepi", "immunization"]):
        if lang == "sw":
            return (
                "**Ratiba ya Chanjo ya Kenya (KEPI)**\n\n"
                "Programu ya KEPI ya Kenya inatoa chanjo zifuatazo bila malipo:\n\n"
                "- **Kuzaliwa:** BCG, OPV 0\n"
                "- **Wiki 6:** Pentavalent 1, OPV 1, PCV10 1, Rotavirus 1\n"
                "- **Wiki 10:** Pentavalent 2, OPV 2, PCV10 2, Rotavirus 2\n"
                "- **Wiki 14:** Pentavalent 3, OPV 3, PCV10 3, IPV\n"
                "- **Miezi 9:** Measles-Rubella 1, Vitamin A, Yellow Fever\n"
                "- **Miezi 18:** Measles-Rubella 2, Vitamin A 2\n\n"
                "Tumia **Ukaguzi wa Chanjo** (kwenye menyu ya kushoto) kupata ratiba ya mtoto wako."
            )
        return (
            "**Kenya KEPI Immunization Schedule**\n\n"
            "Kenya's KEPI program provides the following vaccines free of charge:\n\n"
            "- **At Birth:** BCG, OPV 0\n"
            "- **6 Weeks:** Pentavalent 1, OPV 1, PCV10 1, Rotavirus 1\n"
            "- **10 Weeks:** Pentavalent 2, OPV 2, PCV10 2, Rotavirus 2\n"
            "- **14 Weeks:** Pentavalent 3, OPV 3, PCV10 3, IPV\n"
            "- **9 Months:** Measles-Rubella 1, Vitamin A, Yellow Fever\n"
            "- **18 Months:** Measles-Rubella 2, Vitamin A 2\n\n"
            "Use the **Immunization Tracker** (left menu) for a personalized schedule."
        )

    # Diarrhea keywords
    if any(kw in msg_lower for kw in ["diarrhea", "diarrhoea", "kuhara", "loose stool"]):
        if lang == "sw":
            return (
                "**Kuharisha — Mwongozo wa MoH Kenya**\n\n"
                "Kuharisha ni sababu kubwa ya vifo vya watoto nchini Kenya.\n\n"
                "**Matibabu ya nyumbani (ORS):**\n"
                "- Mpe mgonjwa maji ya ORS kidogo kidogo mara kwa mara\n"
                "- Endelea kulisha mtoto kama kawaida\n"
                "- Nenda kituo cha afya haraka ikiwa: kuhara zaidi ya mara 3 kwa saa, damu kwenye kinyesi, au mtoto anaonekana dhaifu sana"
            )
        return (
            "**Diarrhoea — Kenya MoH Guidance**\n\n"
            "Diarrhoea is a leading cause of child mortality in Kenya.\n\n"
            "**Home management (ORS):**\n"
            "- Give small, frequent sips of ORS solution\n"
            "- Continue feeding the child normally\n"
            "- Seek care immediately if: more than 3 stools per hour, blood in stool, or the child appears very weak\n\n"
            "**Prepare ORS:** 1 litre clean water + 6 teaspoons sugar + ½ teaspoon salt."
        )

    # Default
    if lang == "sw":
        return (
            "**Linda Afya Health Assistant**\n\n"
            "Asante kwa swali lako. Mfumo wetu wa AI unashauriana na miongozo ya Wizara ya Afya Kenya.\n\n"
            "**KUMBUKA:** Sisi si programu rasmi ya Wizara ya Afya; tahadhari inashauriwa.\n\n"
            "Ninaweza kukusaidia na:\n"
            "- 🩺 **Ukaguzi wa Dalili** — angalia kipaumbele chako cha matibabu\n"
            "- 🏥 **Tafuta Kliniki** — pata kituo cha afya karibu nawe\n"
            "- 💉 **Chanjo** — angalia ratiba ya chanjo ya mtoto wako\n\n"
            "⚠️ Kwa dharura yoyote ya kimatibabu, piga simu **0800 720 021** au nenda hospitali ya karibu nawe mara moja."
        )
    return (
        "**Linda Afya Health Assistant**\n\n"
        "Thank you for your question. Our AI system is grounded in the Kenya Ministry of Health guidelines.\n\n"
        "**NOTE:** We aren't an official Ministry of Health app; caution is advised.\n\n"
        "I can help you with:\n"
        "- 🩺 **Symptom Checker** — assess your triage priority\n"
        "- 🏥 **Clinic Locator** — find the nearest health facility\n"
        "- 💉 **Immunisation Tracker** — check your child's vaccine schedule\n\n"
        "⚠️ For any medical emergency, call **0800 720 021** or go to your nearest hospital immediately."
    )
