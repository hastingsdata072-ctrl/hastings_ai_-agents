# Linda Afya — Architecture

## Overview

Linda Afya is a bilingual (English/Kiswahili) AI health assistant web application aligned with Kenya Ministry of Health (MoH) clinical guidelines. It provides four distinct health services through a single Streamlit interface, routing each request to the appropriate module.

---

## Request flow

```
User (browser)
      │
      ▼
Streamlit UI  (app.py)
      │
      ├── Symptom Checker ──► Triage Engine (tools/triage_engine.py)
      │                            │
      │                            ▼
      │                       RED / YELLOW / GREEN priority
      │                            │
      │                            ▼
      │                       Clinic Locator (data/facilities/facilities.csv)
      │                            │
      │                            ▼
      │                       Nearest facility + Google Maps directions
      │
      ├── Clinic Locator ──► facilities.csv  (13,000+ Kenya MoH facilities)
      │                       Haversine distance calculation
      │
      ├── Immunization Tracker ──► KEPI schedule logic
      │                             (Kenya National Immunization Schedule)
      │
      └── Health Chat ──► OpenRouter API
                               │
                               ▼
                          NVIDIA Nemotron 3 Ultra 550B (free tier)
                               │
                               ▼
                          MoH-grounded response
                          (system prompt references Clinical Guidelines,
                           KEPI schedule, KPHEOC handbook, PHC FAQs)
```

---

## Module responsibilities

| Module | Responsibility |
|---|---|
| `src/app.py` | Streamlit entry point — navigation, session state, page routing |
| `src/pages/symptom_checker.py` | Triage form, priority display, facility finder |
| `src/pages/clinic_locator.py` | Standalone facility search by GPS or county/sub-county |
| `src/pages/immunization_tracker.py` | KEPI schedule tracker by child date of birth |
| `src/pages/health_chat.py` | Free-form AI chat interface |
| `src/rag/bedrock_client.py` | OpenRouter API client with mock fallback |
| `src/tools/triage_engine.py` | Kenya MoH decision matrix — RED/YELLOW/GREEN classification |
| `src/i18n/translations.py` | English/Kiswahili string lookup table |
| `data/facilities/facilities.csv` | 13,000+ Kenya health facilities (KEPH Levels 2–6) |

---

## Triage decision matrix

The triage engine (`tools/triage_engine.py`) evaluates symptoms against the Kenya MoH Community Clinical Guidelines:

```
Input: symptoms list + age + duration_days
          │
          ▼
    Contains RED flag? ──yes──► Priority: RED  (Level 4+ hospital, emergency)
          │
          no
          │
          ▼
    Contains YELLOW flag? ──yes──► Priority: YELLOW  (Level 2–3, within 24h)
    OR duration > 7 days?
          │
          no
          │
          ▼
                              Priority: GREEN  (home management)
```

Special rules:
- Under-5 children: lethargy, not eating, fast breathing auto-escalate to RED
- Any yellow symptom persisting > 7 days escalates to RED

---

## AI model

| Property | Value |
|---|---|
| Provider | OpenRouter |
| Model | `nvidia/nemotron-3-ultra-550b-a55b:free` |
| API | OpenAI-compatible REST (`/v1/chat/completions`) |
| System prompt | Grounded in Kenya MoH Clinical Guidelines Vol. I, KEPI schedule, KPHEOC handbook, PHC FAQs |
| Fallback | Keyword-based mock responses (emergency, malaria, vaccination, diarrhoea) |
| Future deployment | Amazon Bedrock AgentCore |

---

## Data sources

| File | Source | Used by |
|---|---|---|
| `data/facilities/facilities.csv` | Kenya MoH KHIS facility registry | Clinic Locator, Symptom Checker |
| `data/documents/494592185-Clinical-Guidelines-Vol-I-FINAL.pdf` | Kenya MoH | AI system prompt grounding |
| `data/documents/992284468-Kenya-Immunization-Schedule.pdf` | Kenya KEPI / MoH | Immunization Tracker, AI grounding |
| `data/documents/Kenya_Public_Health_Emergency_Operations_Center_KPHEOC_Handbook.pdf` | KPHEOC | AI system prompt grounding |
| `data/documents/PRIMARY HEALTH CARE AWARENESS FAQS.pdf` | Kenya MoH PHC | AI system prompt grounding |

---

## Deployment

- **Current:** Streamlit Community Cloud (`streamlit.app`)
- **Target:** Amazon Bedrock AgentCore (RAG with Bedrock Knowledge Bases for PDF grounding)
- **Region:** `eu-north-1` (AWS project region)
