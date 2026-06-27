# KAVERI — Karnataka AI for Violence, Evidence, and Risk Intelligence

> **KSP Datathon 2025 | Challenge 01 — Intelligent Conversational AI for KSP Crime Database**

A production-grade, real-time crime intelligence platform for Karnataka State Police (KSP) and the State Crime Records Bureau (SCRB). KAVERI enables investigators to query crime data in natural language — including Kannada by voice — and receive actionable intelligence grounded in the official KSP CCTNS database schema.

---

## What is KAVERI?

KAVERI is an AI-powered crime intelligence platform that replaces static dashboards and manual SQL queries. A police officer can sit in front of it, ask questions in Kannada or English, and get immediate, data-backed intelligence — with every answer citing the exact FIR numbers, IPC sections, and data sources used.

**Named after:** Karnataka AI for Violence, Evidence, and Risk Intelligence.

**Built for:** Karnataka State Police | SCRB Datathon 2025

**Deployed on:** Zoho Catalyst (AppSail + DataStore + FileStore + Cache + Cron)

---

## Key Features

| Feature | Description |
|---|---|
| **Natural Language Chatbot** | Ask questions in English or Kannada — KAVERI queries the live FIR database and responds intelligently |
| **Voice Interaction** | Speak in Kannada (`kn-IN`) or English — full voice input and spoken responses |
| **Live Crime Map** | Leaflet.js map of Karnataka with real-time FIR pins updating via WebSocket |
| **Criminal Network Graph** | vis.js interactive network of repeat accused persons and their case connections |
| **Crime Hotspot Detection** | Grid-based density analysis refreshed every 5 minutes across all districts |
| **Predictive Analytics** | XGBoost model forecasting crime risk by district and type for the next 7 days |
| **Automatic Alerts** | Real-time alerts for heinous offences, crime spikes, clusters, and repeat accused |
| **Crime DNA Matching** | Cosine similarity search on BriefFacts embeddings to find similar past cases |
| **PDF Intelligence Reports** | One-click export of full conversation with FIR citations, sources, confidence scores |
| **Explainable AI** | Every KAVERI response shows exactly which tables, CrimeNos, and models it used |
| **Role-Based Access** | Admin / Analyst / Officer / Viewer roles with district-level data scoping |
| **Socio-Demographic Insights** | Crime cross-referenced against census data, poverty rates, youth population, festivals |

---

## Database Schema

KAVERI's database **mirrors the official KSP FIR System ER diagram** provided by the datathon team — the actual CCTNS schema used across Karnataka's 1100+ police stations.

### Core KSP Tables

```
CaseMaster          — Every FIR registered (CrimeNo, GPS, BriefFacts, dates)
ComplainantDetails  — Who filed the complaint
Victim              — Who was harmed (age, gender, linked to FIR)
Accused             — Who is suspected (A1, A2, A3... per FIR)
ArrestSurrender     — Arrest and surrender events
ActSectionAssociation — IPC/BNS/NDPS sections per FIR (e.g. IPC 302, IPC 379)
ChargesheetDetails  — Case outcome (A=Chargesheet, B=False, C=Undetected)
CrimeHead           — Major crime group (Crimes Against Body, Property, Women...)
CrimeSubHead        — Specific crime type (Murder, Theft, Robbery, Cyber Crime...)
```

### Lookup Tables

```
Act / Section / CaseCategory / GravityOffence / CaseStatusMaster
State / District / Unit / UnitType / Rank / Designation / Employee / Court
OccupationMaster / ReligionMaster / CasteMaster
```

### CrimeNo Format (Official KSP Standard)

```
CaseCategoryCode(1) + DistrictID(4) + StationID(4) + Year(4) + Serial(5)
Example FIR: 104430006202600001
```

### KAVERI Platform Tables (additions)

```
CrimeEmbeddings     — Pre-generated BriefFacts embeddings for Crime DNA matching
Hotspots            — District hotspot scores (refreshed every 5 min by Cron)
Predictions         — XGBoost 7-day risk forecasts per district and crime type
Alerts              — Fired by alert engine, pushed via WebSocket
Conversations       — Full audit trail of every KAVERI chat session
KAVERIUsers         — Platform RBAC (maps Employee to Admin/Analyst/Officer/Viewer)
DistrictDemographics — Census data, poverty %, youth %, migrant % per district
SeasonalPatterns    — Festival crime multipliers (Navaratri, Deepavali, Ugadi...)
SCRBStats           — Real KSP SCRB 2022/2023/2024 public domain crime statistics
```

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      ZOHO CATALYST PROJECT                         │
│                                                                    │
│  ┌─────────────────┐    ┌────────────────────────────────────────┐ │
│  │  Web Client     │    │  AppSail (Python / Tornado + FastAPI)  │ │
│  │  React 18+Vite  │◄──►│  KAVERI REST API + WebSocket Server    │ │
│  │  Catalyst Static│    │  Port 9000                             │ │
│  └─────────────────┘    └──────────┬─────────────────────────────┘ │
│                                    │                               │
│  ┌─────────────┐  ┌────────────────┴───────┐  ┌─────────────────┐ │
│  │Catalyst     │  │Catalyst DataStore      │  │Catalyst         │ │
│  │Cache        │  │(ZCQL — official KSP    │  │FileStore        │ │
│  │live events  │  │ CCTNS schema)          │  │embeddings JSON  │ │
│  │hotspot data │  │                        │  │ML model pickle  │ │
│  │session state│  │                        │  │PDF reports      │ │
│  └─────────────┘  └────────────────────────┘  └─────────────────┘ │
│                                                                    │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐   │
│  │Catalyst Signals      │  │Catalyst Cron                     │   │
│  │new FIR → alert pipe  │  │hotspot refresh every 5 min       │   │
│  └──────────────────────┘  │prediction refresh every 30 min   │   │
│                            └──────────────────────────────────┘   │
│  External: Claude API (claude-sonnet-4-6) — KAVERI AI engine      │
└────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Backend (Zoho Catalyst AppSail — Python 3.11)

| Library | Purpose |
|---|---|
| `tornado==6.4` | WebSocket server + async runtime |
| `fastapi==0.110` | REST API |
| `uvicorn` | ASGI server |
| `zoho-catalyst-sdk` | DataStore, Cache, FileStore, Auth, Signals |
| `anthropic` | Claude API client (KAVERI engine) |
| `langdetect` | Kannada / English language detection |
| `scikit-learn` | Cosine similarity for Crime DNA |
| `joblib` | Load pre-trained XGBoost from FileStore |
| `reportlab` | PDF intelligence report generation |
| `python-jose` | JWT validation |
| `pydantic` | Request/response models |

### Frontend (Zoho Catalyst Web Client — React 18)

| Library | Purpose |
|---|---|
| React 18 + Vite | Core UI framework |
| Tailwind CSS | Styling |
| Leaflet.js + leaflet.heat | Karnataka crime heatmap |
| vis-network | Criminal network graph |
| recharts | Trend charts + threat radar |
| i18next | English / Kannada translations |
| Web Speech API | Voice input (browser-native, Chrome) |

### Offline / Seed Scripts (Run locally, NOT on Catalyst)

| Library | Purpose |
|---|---|
| `sentence-transformers` | Generate crime DNA embeddings |
| `xgboost` + `lightgbm` | Train prediction model |
| `shap` | SHAP explanations for predictions |
| `pandas` | Process real KSP SCRB CSV data |

---

## Project Structure

```
kaveri/
├── catalyst.json                     ← Auto-generated by Catalyst CLI
├── .env                              ← Secrets (never commit)
├── .gitignore
├── README.md
│
├── backend/                          ← AppSail (Python 3.11 / Tornado)
│   ├── app.py                        ← Entry point (Tornado + FastAPI)
│   ├── requirements.txt
│   ├── ai/
│   │   ├── kaveri_engine.py          ← KAVERI Claude conversational engine
│   │   └── crime_dna.py              ← Cosine similarity Crime DNA matching
│   ├── alerts/
│   │   └── alert_engine.py           ← Alert rules (HEINOUS, SPIKE, CLUSTER, REPEAT)
│   ├── auth/
│   │   └── rbac.py                   ← Role-based access control
│   ├── api/
│   │   ├── webhook.py                ← Production FIR ingest endpoint
│   │   ├── firs.py                   ← CaseMaster API
│   │   ├── network.py                ← Repeat accused network graph
│   │   ├── hotspots.py               ← Hotspot queries
│   │   ├── predictions.py            ← XGBoost prediction queries
│   │   ├── alerts.py                 ← Alert CRUD
│   │   ├── stats.py                  ← District stats + SCRB data
│   │   └── export.py                 ← PDF report generator
│   └── simulator/
│       └── event_streamer.py         ← Replays seeded FIRs as live feed
│
├── functions/
│   └── cron_refresh/
│       └── index.py                  ← Hotspot + prediction refresh (Catalyst Cron)
│
├── client/                           ← React 18 (Catalyst Web Client)
│   ├── public/
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── KAVERIChat.jsx        ← Chatbot + voice input/output
│       │   ├── CrimeMap.jsx          ← Leaflet Karnataka map
│       │   ├── NetworkGraph.jsx      ← vis.js criminal network
│       │   ├── AlertCenter.jsx       ← Real-time alert feed
│       │   ├── ThreatRadar.jsx       ← District risk gauges
│       │   ├── FIRDetail.jsx         ← Full FIR view (all linked tables)
│       │   └── PredictionPanel.jsx   ← 7-day forecast + SHAP factors
│       ├── hooks/
│       │   ├── useWebSocket.js       ← WebSocket live event hook
│       │   └── useVoiceInput.js      ← Web Speech API hook
│       └── i18n/
│           └── translations.js       ← English + Kannada UI strings
│
└── scripts/                          ← Run LOCALLY — never deployed to Catalyst
    ├── seed_reference_data.py        ← States, Districts, Units, Acts, Sections, Ranks
    ├── seed_fir_data.py              ← SCRB-calibrated FIRs → CaseMaster
    ├── seed_victims_accused.py       ← Victims + Accused linked to FIRs
    ├── seed_demographics.py          ← DistrictDemographics + SeasonalPatterns
    ├── seed_scrb_stats.py            ← Real SCRB 2022/2023/2024 CSV → SCRBStats
    ├── seed_embeddings.py            ← Generate Crime DNA embeddings offline
    └── train_predict.py              ← Train XGBoost + upload predictions
```

---

## Setup and Deployment

### Prerequisites

- Node.js 18+
- Python 3.11+
- Zoho Catalyst account with 1500+ credits
- Anthropic API key
- Chrome browser (for voice input)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/kaveri-ksp.git
cd kaveri-ksp
```

### 2. Configure environment variables

Create a `.env` file in the root directory:

```env
ANTHROPIC_API_KEY=sk-ant-your-key-here
JWT_SECRET=your-strong-jwt-secret
CATALYST_PROJECT_ID=your-project-id
CATALYST_ENV=production
```

> ⚠️ Never commit `.env` to GitHub. It is listed in `.gitignore`.

### 3. Install Catalyst CLI and login

```bash
npm install -g zoho-catalyst-cli
catalyst login
catalyst init
```

### 4. Run seed scripts locally

These scripts generate and upload data to Catalyst DataStore. Run them once before deploying.

```bash
cd scripts

# Step 1: Reference data (districts, crime types, ranks, courts)
python seed_reference_data.py        # ~2 minutes

# Step 2: FIR records calibrated to real SCRB 2024 data
python seed_fir_data.py              # ~15 minutes

# Step 3: Victims and accused linked to each FIR
python seed_victims_accused.py       # ~10 minutes

# Step 4: District demographics and seasonal patterns
python seed_demographics.py          # ~1 minute

# Step 5: Real SCRB 2022/2023/2024 statistics
python seed_scrb_stats.py            # ~2 minutes

# Step 6: Crime DNA embeddings (sentence-transformers, offline only)
python seed_embeddings.py            # ~20 minutes

# Step 7: Train XGBoost prediction model and upload results
python train_predict.py              # ~10 minutes
```

### 5. Deploy to Zoho Catalyst

```bash
# Deploy backend (AppSail)
cd backend
catalyst deploy --service appsail --name kaveri-backend

# Deploy frontend (Web Client)
cd ../client
npm install
npm run build
catalyst deploy --service web-client

# Deploy cron function
cd ../functions/cron_refresh
catalyst deploy --service function --type cron
```

### 6. Set environment variables in Catalyst Console

Go to your Catalyst project → AppSail → Environment Variables and add:
- `ANTHROPIC_API_KEY`
- `JWT_SECRET`
- `CATALYST_PROJECT_ID`
- `CATALYST_ENV`

---

## Data Sources

| Source | Type | Usage |
|---|---|---|
| KSP SCRB Crime Review 2024 | Real public domain CSV | District-wise IPC crime counts (38 districts, 21 crime types) |
| KSP SCRB Crime Review 2023 | Real public domain CSV | Year-over-year trend analysis |
| KSP SCRB Crime Review 2022 | Real public domain CSV | 3-year historical baseline |
| Synthetic FIR records | Generated | Individual FIR records with GPS, victim, accused — calibrated to match real SCRB counts |
| Karnataka Census data | Reference | District demographics (population, poverty, literacy, youth %) |

> Real SCRB data is sourced from [data.opencity.in](https://data.opencity.in/dataset/karnataka-crime-data-2024) published by Bengaluru City Police under Public Domain licence, sourced from `ksp.karnataka.gov.in`.

---

## How KAVERI Answers Questions

KAVERI classifies every query into one of these intents and queries the relevant tables:

| Intent | Example Query | Tables Used |
|---|---|---|
| `HOTSPOT_QUERY` | "Where are the crime hotspots in Bengaluru?" | CaseMaster + Unit + District |
| `ACCUSED_QUERY` | "Who are the repeat offenders in Mysuru?" | Accused + CaseMaster + CrimeSubHead |
| `VICTIM_QUERY` | "What is the victim profile for cyber crime?" | Victim + CaseMaster + District |
| `ARREST_QUERY` | "Show recent arrests in Belagavi" | ArrestSurrender + Accused + CaseMaster |
| `TREND_QUERY` | "ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳ್ಳತನ ಏಕೆ ಹೆಚ್ಚಾಗುತ್ತಿದೆ?" | CaseMaster + CrimeSubHead (monthly) |
| `PREDICTION_QUERY` | "What crimes are predicted next week?" | Predictions (XGBoost output) |
| `NETWORK_QUERY` | "Show criminal network in Kalaburagi" | Accused (multi-case repeat offenders) |
| `CHARGESHEET_QUERY` | "How many cases were chargesheeted?" | ChargesheetDetails + CaseMaster |
| `PATROL_RECOMMENDATION` | "Where should I deploy patrol tonight?" | Hotspots + Predictions |
| `DEMOGRAPHIC_QUERY` | "Which districts have highest crime per lakh?" | DistrictDemographics + CaseMaster |
| `SEASONAL_QUERY` | "Why do crimes spike in October?" | SeasonalPatterns + CaseMaster monthly |

---

## Alert Engine

KAVERI automatically monitors incoming FIRs and fires alerts:

| Alert | Trigger | Severity |
|---|---|---|
| `HEINOUS_OFFENCE` | New FIR with GravityOffenceID = 1 (murder, rape) | CRITICAL |
| `CRIME_SPIKE` | 5+ FIRs of same crime type in same district within 8 hours | HIGH |
| `CLUSTER_ALERT` | 3+ FIRs within ~2km radius in 4 hours | HIGH |
| `REPEAT_ACCUSED` | AccusedName in new FIR matches existing accused in database | CRITICAL |

All alerts are pushed instantly to all connected officers via WebSocket.

---

## KAVERI Chat Examples

**English:**
```
Officer: Show me the top crime hotspots in Bengaluru Urban this week
         and which accused are linked to multiple cases.

KAVERI:  Based on CaseMaster records for Bengaluru Urban (last 7 days):
         Top hotspot: Whitefield area — 47 FIRs (23 theft, 12 robbery, 12 cyber fraud)
         Repeat accused: Ravi Kumar (A1 in FIR KAR-2024-BEU-00891, 00934, 01102)
         Recommendation: Deploy additional patrol near Whitefield IT corridor
         between 8pm–2am. Focus on vehicle theft and chain snatching.
         Sources: CaseMaster + Accused + District | Confidence: HIGH
```

**Kannada:**
```
ಅಧಿಕಾರಿ: ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳ್ಳತನ ಏಕೆ ಹೆಚ್ಚಾಗುತ್ತಿದೆ?

KAVERI:  ಬೆಂಗಳೂರು ನಗರದಲ್ಲಿ 2024ರಲ್ಲಿ 9,605 ಕಳ್ಳತನ ಪ್ರಕರಣಗಳು ದಾಖಲಾಗಿವೆ.
         ಅಕ್ಟೋಬರ್-ನವೆಂಬರ್ ತಿಂಗಳಲ್ಲಿ ನವರಾತ್ರಿ ಮತ್ತು ದೀಪಾವಳಿ ಹಬ್ಬಗಳ
         ಸಮಯದಲ್ಲಿ 1.5 ಪಟ್ಟು ಹೆಚ್ಚಳ ಕಂಡುಬಂದಿದೆ. ವ್ಹೈಟ್‌ಫೀಲ್ಡ್ ಮತ್ತು
         ಎಲೆಕ್ಟ್ರಾನಿಕ್ ಸಿಟಿ ಪ್ರದೇಶಗಳಲ್ಲಿ ಹೆಚ್ಚಿನ ಪ್ರಮಾಣ ಕಂಡುಬಂದಿದೆ.
         ಮೂಲ: CaseMaster + SeasonalPatterns | ವಿಶ್ವಾಸ: ಅಧಿಕ
```

---

## Production Webhook

The `/webhook/fir/ingest` endpoint accepts new FIRs in the official KSP CCTNS field format. In the demo, the "Simulate New FIR" button calls this exact endpoint.

```
In production: KSP's CCTNS system POSTs to this endpoint when a new FIR
               is registered at any of the 1100+ police stations.

In demo:       The "Simulate New Crime" button calls this same endpoint,
               demonstrating the identical production data path.
```

Connecting to live KSP systems requires one URL change — the schema is already identical to CCTNS.

---

## Credit Budget (Zoho Catalyst)

| Service | Estimated Usage |
|---|---|
| AppSail (backend during demo, ~4 hrs) | ~200 credits |
| Catalyst Functions (cron, ~20 runs) | ~20 credits |
| DataStore reads (~500 chatbot queries) | ~50 credits |
| DataStore writes (seed + demo events) | ~100 credits |
| FileStore (embeddings + PDF reports) | ~30 credits |
| Web Client hosting | ~50 credits |
| Catalyst Cache (event queue) | ~20 credits |
| **Total estimated** | **~470 credits** |
| **Budget remaining** | **~1030 credits** |

---

## Pre-Demo Checklist

- [ ] All reference tables seeded (States, Districts, Units, Acts, Sections)
- [ ] CaseMaster seeded with SCRB-calibrated FIR records
- [ ] Victim + Accused tables linked to CaseMaster by CaseMasterID
- [ ] ActSectionAssociation seeded (IPC/BNS sections per FIR)
- [ ] ChargesheetDetails seeded (A/B/C outcomes)
- [ ] DistrictDemographics + SeasonalPatterns seeded
- [ ] SCRBStats loaded with real 2022/2023/2024 data
- [ ] Crime DNA embeddings uploaded to Catalyst FileStore
- [ ] XGBoost predictions loaded into Predictions table
- [ ] AppSail backend deployed and reachable
- [ ] WebSocket connects in Chrome (no console errors)
- [ ] English chatbot tested with 5 different question types
- [ ] Kannada chatbot tested — Kannada input gets Kannada response
- [ ] Voice input works in Chrome (English + Kannada)
- [ ] vis.js network graph loads and is clickable
- [ ] Alert fires when demo FIR is injected
- [ ] PDF export generates clean report with CrimeNos + sources
- [ ] Language toggle switches all UI text (EN ↔ ಕನ್ನಡ)
- [ ] RBAC login works (Admin sees all, Officer sees own district)
- [ ] Map zooms to district when alert is clicked
- [ ] Keep browser tab open pinging backend every 3 min before demo (prevents cold start)

---

## Team

Built for the KSP Datathon 2025 — Challenge 01: Intelligent Conversational AI for KSP Crime Database.

---

## Disclaimer

This platform uses:
- Real Karnataka SCRB crime statistics (Public Domain, sourced from `ksp.karnataka.gov.in` via `data.opencity.in`)
- Synthetic individual FIR records calibrated to match real district crime counts
- The official KSP CCTNS database schema provided by the datathon team

This is a datathon prototype. It is not connected to live KSP systems. No real personal data of victims, accused, or officers is used.

---

## License

This project is submitted for the KSP Datathon 2025. All rights reserved.# kKSP-INTELLIGENCE-CRIME
