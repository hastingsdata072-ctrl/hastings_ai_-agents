# Linda Afya Health Assistant
### Built with Streamlit · OpenRouter · NVIDIA Nemotron · Kenya MoH Guidelines

A bilingual (English/Kiswahili) AI-powered health assistant aligned with Kenya Ministry of Health (MoH) clinical protocols. It provides symptom triage, clinic location, immunization tracking, and free-form AI health chat — all grounded in official MoH documents.

> ⚠️ This is a prototype, not an official MoH application. Not for real medical use. Always consult a qualified healthcare provider.

**Live app:** [linda-afya.streamlit.app](https://linda-afya.streamlit.app)

---

## What it does

| Feature | Description |
|---|---|
| 🩺 **Symptom Checker** | Evaluates symptoms against Kenya MoH decision matrix → RED / YELLOW / GREEN triage priority + nearest appropriate facility |
| 🏥 **Clinic Locator** | Finds the nearest health facility from 13,000+ Kenya MoH facilities by GPS coordinates or county/sub-county |
| 💉 **Immunization Tracker** | Tracks child vaccination milestones against the Kenya KEPI schedule by date of birth |
| 💬 **Health Chat** | Free-form AI chat grounded in MoH Clinical Guidelines, KEPI schedule, KPHEOC handbook, and PHC FAQs |

Both English and Kiswahili are fully supported across all four features.

---

## Architecture

```
User (browser)
      │
      ▼
Streamlit UI  (src/app.py)
      │
      ├── Symptom Checker ──► Triage Engine → RED/YELLOW/GREEN → Nearest facility
      ├── Clinic Locator  ──► facilities.csv (Haversine distance)
      ├── Immunization    ──► KEPI schedule logic
      └── Health Chat     ──► OpenRouter API → NVIDIA Nemotron 3 Ultra 550B
                                                    │
                                               MoH-grounded response
```

See [architecture.md](./architecture.md) for full module responsibilities and request flow.

---

## Stack

| Layer | Technology |
|---|---|
| UI framework | Streamlit |
| AI model | NVIDIA Nemotron 3 Ultra 550B (via OpenRouter) |
| API | OpenRouter `/v1/chat/completions` (OpenAI-compatible) |
| Data processing | pandas, numpy |
| Maps | folium, Google Maps directions links |
| Language | Python 3.12 |
| Deployment | Streamlit Community Cloud |
| Future deployment | Amazon Bedrock AgentCore |

---

## Repository layout

```
linda-afya/
├── README.md
├── architecture.md
├── requirements.txt
├── .python-version             # pins Python 3.12 for Streamlit Cloud
├── .env.example
│
├── src/                        # Application source code
│   ├── app.py                  # Streamlit entry point — navigation, routing
│   ├── pages/
│   │   ├── symptom_checker.py  # Triage form + facility finder
│   │   ├── clinic_locator.py   # Standalone facility search
│   │   ├── immunization_tracker.py  # KEPI schedule tracker
│   │   └── health_chat.py      # AI chat interface
│   ├── rag/
│   │   └── bedrock_client.py   # OpenRouter client + mock fallback
│   ├── tools/
│   │   └── triage_engine.py    # Kenya MoH decision matrix logic
│   └── i18n/
│       └── translations.py     # English / Kiswahili string table
│
├── data/
│   ├── facilities/
│   │   ├── facilities.csv      # 13,000+ Kenya MoH health facilities
│   │   └── kenya_hospitals.csv # Hospital subset
│   └── documents/              # MoH reference PDFs (RAG knowledge base)
│       ├── 494592185-Clinical-Guidelines-Vol-I-FINAL.pdf
│       ├── 992284468-Kenya-Immunization-Schedule.pdf
│       ├── Kenya_Public_Health_Emergency_Operations_Center_KPHEOC_Handbook.pdf
│       └── PRIMARY HEALTH CARE AWARENESS FAQS.pdf
│
├── infra/                      # Future: Bedrock Knowledge Base + AgentCore IaC
└── docs/
    └── screenshots/            # App screenshots
```

---

## Setup and running locally

**Prerequisites**
- Python 3.12
- An [OpenRouter](https://openrouter.io) API key

**1 — Install dependencies**
```bash
cd linda-afya
pip install -r requirements.txt
```

**2 — Configure secrets**
```bash
mkdir -p src/.streamlit
# Create src/.streamlit/secrets.toml with:
# OPENROUTER_API_KEY = "your-key-here"
```

**3 — Run**
```bash
streamlit run src/app.py
```

---

## Deployment (Streamlit Cloud)

1. Fork or push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
3. Set main file path to `src/app.py`
4. Under **Advanced settings → Secrets**, add:
```toml
OPENROUTER_API_KEY = "your-key-here"
```
5. Set Python version to **3.12**
6. Click **Deploy**

---

## Triage decision matrix

The triage engine evaluates symptoms against Kenya MoH Community Clinical Guidelines:

| Priority | Criteria | Recommended action |
|---|---|---|
| 🔴 RED | Danger signs detected (convulsions, severe breathing difficulty, unconsciousness, severe bleeding, etc.) | Level 4+ hospital immediately — call 0800 720 021 |
| 🟡 YELLOW | Urgent symptoms (fever, cough, diarrhoea, etc.) or symptoms > 7 days | Level 2–3 facility within 24 hours |
| 🟢 GREEN | No danger or urgent signs | Home management, contact Community Health Promoter |

Special rules:
- Under-5 children: lethargy, not eating, fast breathing auto-escalate to RED
- Any yellow symptom lasting > 7 days escalates to RED

---

## Key engineering decisions

**Keyword-free triage**
The triage engine uses a curated symptom list derived from the Kenya MoH Community Clinical Guidelines Vol. I, not ML classification. This makes it auditable, explainable, and easy to update as guidelines change.

**Haversine distance for facility matching**
Straight-line distance using Haversine formula gives a fast, serverless approximation. The UI clearly labels results as "straight-line" and notes that actual travel may be longer.

**MoH-grounded system prompt**
The AI system prompt explicitly references the four MoH source documents. The model is instructed to never diagnose, never provide drug dosages, and always end with a referral recommendation. Safety rules are listed as hard constraints.

**Mock fallback**
If the OpenRouter API is unavailable, a keyword-based fallback provides safe, MoH-aligned responses for the most common health scenarios (emergency, malaria, vaccination, diarrhoea). This ensures the app is always usable.

**Bilingual by design**
All UI strings are managed in `i18n/translations.py`. The AI model responds in the language the user writes in. Emergency numbers and facility data are language-agnostic.

---

## Emergency contacts (hardcoded)

| Line | Number |
|---|---|
| Kenya Health Emergency | 0800 720 021 (free, 24/7) |
| Red Cross | 0800 723 253 (free) |
| Police / Ambulance | 999 |
| Pan-Africa Emergency | 112 |

---

## Future work

- **Bedrock Knowledge Base RAG** — embed the 4 MoH PDFs into a Bedrock Knowledge Base for retrieval-augmented generation, replacing the current system-prompt-only grounding
- **AgentCore deployment** — migrate to Amazon Bedrock AgentCore for production-grade managed inference
- **Clinical validation** — formal review by Kenya MoH-registered clinicians
- **Data protection compliance** — align with Kenya Data Protection Act 2019
- **Authentication** — user accounts for persistent immunization records
- **Offline mode** — progressive web app for low-connectivity environments

---

## License

Udacity Project License
