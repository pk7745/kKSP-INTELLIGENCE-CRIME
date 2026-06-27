import os
import json
import logging
import uuid
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

logger = logging.getLogger("kaveri.engine")

router = APIRouter()

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Intent classification keywords
INTENT_PATTERNS = {
    "HOTSPOT_QUERY": [
        "hotspot", "hotspots", "cluster", "concentration", "area", "zone",
        "where", "location", "map", "ಹಾಟ್ಸ್ಪಾಟ್", "ಪ್ರದೇಶ",
    ],
    "ACCUSED_QUERY": [
        "accused", "offender", "repeat", "criminal", "suspect", "arrested",
        "ಆರೋಪಿ", "ಅಪರಾಧಿ",
    ],
    "VICTIM_QUERY": [
        "victim", "victims", "complainant", "survivor", "age", "gender",
        "ಸಂತ್ರಸ್ತ", "ಬಲಿಪಶು",
    ],
    "ARREST_QUERY": [
        "arrest", "arrested", "custody", "detained", "surrender",
        "ಬಂಧನ", "ಬಂಧಿಸ",
    ],
    "TREND_QUERY": [
        "trend", "increase", "decrease", "rising", "falling", "monthly", "weekly",
        "year", "compared", "ಹೆಚ್ಚಾಗುತ್ತಿದೆ", "ಇಳಿಕೆ", "ಏರಿಕೆ",
    ],
    "PREDICTION_QUERY": [
        "predict", "forecast", "next week", "future", "expected", "risk",
        "ಮುನ್ಸೂಚನೆ", "ಮುಂದಿನ",
    ],
    "NETWORK_QUERY": [
        "network", "gang", "connection", "linked", "associated", "group",
        "ಜಾಲ", "ಗ್ಯಾಂಗ್",
    ],
    "CHARGESHEET_QUERY": [
        "chargesheet", "charge sheet", "outcome", "verdict", "filed", "undetected",
        "ದೋಷಾರೋಪಣೆ", "ಫಲಿತಾಂಶ",
    ],
    "PATROL_RECOMMENDATION": [
        "patrol", "deploy", "where should", "recommendation", "tonight",
        "ಗಸ್ತು", "ನಿಯೋಜಿಸಿ",
    ],
    "DEMOGRAPHIC_QUERY": [
        "demographic", "population", "poverty", "youth", "census", "per lakh",
        "ಜನಸಂಖ್ಯೆ", "ಬಡತನ",
    ],
    "SEASONAL_QUERY": [
        "festival", "seasonal", "diwali", "navratri", "ugadi", "october",
        "november", "ಹಬ್ಬ", "ನವರಾತ್ರಿ", "ದೀಪಾವಳಿ",
    ],
}


class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    district_filter: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    intent: str
    language: str
    sources: List[str]
    confidence: str
    session_id: str


def detect_language(text: str) -> str:
    """Detect if query is Kannada or English."""
    try:
        from langdetect import detect
        lang = detect(text)
        return lang
    except Exception:
        # Fallback: check for Kannada Unicode range (U+0C80–U+0CFF)
        kannada_chars = sum(1 for c in text if "ಀ" <= c <= "೿")
        if kannada_chars > 2:
            return "kn"
        return "en"


def classify_intent(query: str) -> str:
    """Classify query intent based on keyword matching."""
    query_lower = query.lower()
    scores = {}
    for intent, keywords in INTENT_PATTERNS.items():
        score = sum(1 for kw in keywords if kw in query_lower)
        if score > 0:
            scores[intent] = score
    if not scores:
        return "TREND_QUERY"
    return max(scores, key=scores.get)


def get_catalyst_client():
    """Get Catalyst DataStore client or None if not configured."""
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


async def query_datastore_for_intent(
    intent: str, district_filter: Optional[str], query: str
) -> tuple[list, list]:
    """Query Catalyst DataStore based on intent. Returns (data, sources)."""
    datastore = get_catalyst_client()

    # Fallback mock data when DataStore is not configured
    if datastore is None:
        return _mock_data_for_intent(intent, district_filter), _sources_for_intent(intent)

    sources = _sources_for_intent(intent)
    data = []

    district_clause = f"AND DistrictID = '{district_filter}'" if district_filter else ""

    try:
        if intent == "HOTSPOT_QUERY":
            zcql = f"""SELECT DistrictID, DistrictName, lat, lng, score, crimeCount, dominantCrimeType
                       FROM Hotspots ORDER BY score DESC LIMIT 10"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "ACCUSED_QUERY":
            zcql = f"""SELECT AccusedName, COUNT(ROWID) as CaseCount, DistrictID
                       FROM Accused {district_clause.replace('AND', 'WHERE') if district_clause else ''}
                       GROUP BY AccusedName HAVING CaseCount > 1
                       ORDER BY CaseCount DESC LIMIT 20"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "VICTIM_QUERY":
            zcql = f"""SELECT v.Age, v.Gender, v.Occupation, c.CrimeSubHeadID, c.DistrictID
                       FROM Victim v JOIN CaseMaster c ON v.CaseMasterID = c.ROWID
                       WHERE 1=1 {district_clause} LIMIT 100"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "ARREST_QUERY":
            zcql = f"""SELECT a.AccusedName, ar.ArrestDate, ar.ArrestingOfficerID, c.CrimeNo, c.DistrictID
                       FROM ArrestSurrender ar
                       JOIN Accused a ON ar.AccusedID = a.ROWID
                       JOIN CaseMaster c ON a.CaseMasterID = c.ROWID
                       WHERE 1=1 {district_clause} ORDER BY ar.ArrestDate DESC LIMIT 20"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "TREND_QUERY":
            zcql = f"""SELECT CrimeSubHeadID, DistrictID, COUNT(ROWID) as Count,
                       SUBSTR(CrimeDateTime, 1, 7) as Month
                       FROM CaseMaster WHERE 1=1 {district_clause}
                       GROUP BY CrimeSubHeadID, DistrictID, Month
                       ORDER BY Month DESC LIMIT 50"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "PREDICTION_QUERY":
            zcql = f"""SELECT DistrictID, DistrictName, CrimeType, RiskScore, PredictedCount, date, shap_factors
                       FROM Predictions WHERE 1=1 {district_clause}
                       ORDER BY RiskScore DESC LIMIT 20"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "NETWORK_QUERY":
            zcql = f"""SELECT AccusedName, COUNT(DISTINCT CaseMasterID) as CaseCount, DistrictID
                       FROM Accused WHERE 1=1 {district_clause.replace('AND', 'WHERE')}
                       GROUP BY AccusedName HAVING CaseCount >= 2
                       ORDER BY CaseCount DESC LIMIT 30"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "CHARGESHEET_QUERY":
            zcql = f"""SELECT cd.ChargesheetStatus, COUNT(cd.ROWID) as Count, c.DistrictID
                       FROM ChargesheetDetails cd
                       JOIN CaseMaster c ON cd.CaseMasterID = c.ROWID
                       WHERE 1=1 {district_clause}
                       GROUP BY cd.ChargesheetStatus, c.DistrictID"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "PATROL_RECOMMENDATION":
            zcql = f"""SELECT DistrictID, DistrictName, lat, lng, score, crimeCount, dominantCrimeType
                       FROM Hotspots ORDER BY score DESC LIMIT 5"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "DEMOGRAPHIC_QUERY":
            zcql = f"""SELECT DistrictName, Population, PovertyRate, YouthRate, LiteracyRate,
                       MigrantRate, CrimesPerLakh FROM DistrictDemographics LIMIT 30"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

        elif intent == "SEASONAL_QUERY":
            zcql = """SELECT FestivalName, Month, CrimeMultiplier, AffectedCrimeTypes, Districts
                      FROM SeasonalPatterns ORDER BY CrimeMultiplier DESC"""
            result = datastore.execute_query(zcql)
            data = result.get("data", [])

    except Exception as e:
        logger.warning(f"DataStore query failed for intent {intent}: {e}")
        data = _mock_data_for_intent(intent, district_filter)

    return data, sources


def _sources_for_intent(intent: str) -> list:
    mapping = {
        "HOTSPOT_QUERY": ["CaseMaster", "Hotspots", "District"],
        "ACCUSED_QUERY": ["Accused", "CaseMaster", "CrimeSubHead"],
        "VICTIM_QUERY": ["Victim", "CaseMaster", "District"],
        "ARREST_QUERY": ["ArrestSurrender", "Accused", "CaseMaster"],
        "TREND_QUERY": ["CaseMaster", "CrimeSubHead", "SCRBStats"],
        "PREDICTION_QUERY": ["Predictions", "XGBoost Model"],
        "NETWORK_QUERY": ["Accused", "CaseMaster"],
        "CHARGESHEET_QUERY": ["ChargesheetDetails", "CaseMaster"],
        "PATROL_RECOMMENDATION": ["Hotspots", "Predictions"],
        "DEMOGRAPHIC_QUERY": ["DistrictDemographics", "CaseMaster"],
        "SEASONAL_QUERY": ["SeasonalPatterns", "CaseMaster"],
    }
    return mapping.get(intent, ["CaseMaster"])


def _mock_data_for_intent(intent: str, district_filter: Optional[str]) -> list:
    """Return mock data for local development without Catalyst."""
    mock = {
        "HOTSPOT_QUERY": [
            {"DistrictID": "BEU", "DistrictName": "Bengaluru Urban", "lat": 12.9716, "lng": 77.5946, "score": 92, "crimeCount": 1247, "dominantCrimeType": "Theft"},
            {"DistrictID": "MYS", "DistrictName": "Mysuru", "lat": 12.2958, "lng": 76.6394, "score": 71, "crimeCount": 634, "dominantCrimeType": "Robbery"},
            {"DistrictID": "KLB", "DistrictName": "Kalaburagi", "lat": 17.3297, "lng": 76.8200, "score": 68, "crimeCount": 521, "dominantCrimeType": "Murder"},
        ],
        "ACCUSED_QUERY": [
            {"AccusedName": "Ravi Kumar", "CaseCount": 5, "DistrictID": "BEU"},
            {"AccusedName": "Mohammed Imran", "CaseCount": 4, "DistrictID": "MYS"},
            {"AccusedName": "Suresh Naik", "CaseCount": 3, "DistrictID": "BEU"},
        ],
        "VICTIM_QUERY": [
            {"Age": 28, "Gender": "F", "Occupation": "Student", "CrimeSubHeadID": "EVE_TEAS", "DistrictID": "BEU"},
            {"Age": 45, "Gender": "M", "Occupation": "Businessman", "CrimeSubHeadID": "THEFT", "DistrictID": "MYS"},
        ],
        "ARREST_QUERY": [
            {"AccusedName": "Ravi Kumar", "ArrestDate": "2024-10-15", "CrimeNo": "1BEU0001202400001", "DistrictID": "BEU"},
            {"AccusedName": "Suresh Naik", "ArrestDate": "2024-10-14", "CrimeNo": "1BEU0002202400002", "DistrictID": "BEU"},
        ],
        "TREND_QUERY": [
            {"CrimeSubHeadID": "THEFT", "DistrictID": "BEU", "Count": 847, "Month": "2024-10"},
            {"CrimeSubHeadID": "THEFT", "DistrictID": "BEU", "Count": 712, "Month": "2024-09"},
            {"CrimeSubHeadID": "ROBBERY", "DistrictID": "BEU", "Count": 234, "Month": "2024-10"},
        ],
        "PREDICTION_QUERY": [
            {"DistrictID": "BEU", "DistrictName": "Bengaluru Urban", "CrimeType": "Theft", "RiskScore": 0.89, "PredictedCount": 145, "date": "2024-11-01", "shap_factors": "Festival season, high foot traffic"},
            {"DistrictID": "MYS", "DistrictName": "Mysuru", "CrimeType": "Robbery", "RiskScore": 0.74, "PredictedCount": 52, "date": "2024-11-01", "shap_factors": "Weekend, low patrol density"},
        ],
        "NETWORK_QUERY": [
            {"AccusedName": "Ravi Kumar", "CaseCount": 5, "DistrictID": "BEU"},
            {"AccusedName": "Suresh Naik", "CaseCount": 3, "DistrictID": "BEU"},
        ],
        "CHARGESHEET_QUERY": [
            {"ChargesheetStatus": "A", "Count": 3421, "DistrictID": "BEU"},
            {"ChargesheetStatus": "B", "Count": 412, "DistrictID": "BEU"},
            {"ChargesheetStatus": "C", "Count": 987, "DistrictID": "BEU"},
        ],
        "PATROL_RECOMMENDATION": [
            {"DistrictID": "BEU", "DistrictName": "Bengaluru Urban", "lat": 12.9716, "lng": 77.5946, "score": 92, "crimeCount": 1247, "dominantCrimeType": "Theft"},
        ],
        "DEMOGRAPHIC_QUERY": [
            {"DistrictName": "Bengaluru Urban", "Population": 12000000, "PovertyRate": 8.2, "YouthRate": 34.1, "LiteracyRate": 89.5, "MigrantRate": 42.3, "CrimesPerLakh": 412},
            {"DistrictName": "Kalaburagi", "Population": 2800000, "PovertyRate": 24.7, "YouthRate": 38.2, "LiteracyRate": 62.1, "MigrantRate": 12.1, "CrimesPerLakh": 186},
        ],
        "SEASONAL_QUERY": [
            {"FestivalName": "Navaratri", "Month": 10, "CrimeMultiplier": 1.52, "AffectedCrimeTypes": "Theft, Chain Snatching", "Districts": "BEU, MYS, BMR"},
            {"FestivalName": "Deepavali", "Month": 11, "CrimeMultiplier": 1.47, "AffectedCrimeTypes": "Theft, Burglary", "Districts": "All"},
            {"FestivalName": "Ugadi", "Month": 3, "CrimeMultiplier": 1.21, "AffectedCrimeTypes": "Assault, Drunk Driving", "Districts": "All"},
        ],
    }
    results = mock.get(intent, [])
    if district_filter and results:
        filtered = [r for r in results if r.get("DistrictID") == district_filter]
        return filtered if filtered else results
    return results


def build_system_prompt(
    intent: str, data: list, sources: list, language: str
) -> str:
    data_context = json.dumps(data, indent=2, default=str)
    kannada_instruction = (
        "\nIMPORTANT: The user is writing in Kannada. Respond entirely in Kannada (ಕನ್ನಡ). "
        "Use Kannada script for all text including numbers when appropriate."
        if language == "kn"
        else ""
    )

    return f"""You are KAVERI — Karnataka AI for Violence, Evidence, and Risk Intelligence — an AI crime intelligence assistant for Karnataka State Police (KSP) and the State Crime Records Bureau (SCRB).

You help police officers, analysts, and investigators query crime data and get actionable intelligence.

CURRENT DATA CONTEXT (from KSP CCTNS DataStore, intent: {intent}):
```json
{data_context}
```

DATA SOURCES USED: {', '.join(sources)}

INSTRUCTIONS:
1. Base your answer on the data provided above. Do not invent FIR numbers or statistics.
2. Always cite specific FIR numbers (CrimeNo), IPC/BNS sections, district names, and table names when available.
3. Provide actionable intelligence — not just raw data.
4. End every response with: "Sources: {' | '.join(sources)} | Confidence: HIGH/MEDIUM/LOW"
5. If data is empty or limited, say so and explain what would be needed.
6. Format numbers clearly. Use Indian number system (lakhs, crores) where appropriate.
7. Be concise but thorough. Police officers need quick, accurate answers.
{kannada_instruction}

PLATFORM TABLES FOR REFERENCE: CaseMaster, ComplainantDetails, Victim, Accused, ArrestSurrender, ActSectionAssociation, ChargesheetDetails, CrimeHead, CrimeSubHead, District, Unit, CrimeEmbeddings, Hotspots, Predictions, Alerts, Conversations, DistrictDemographics, SeasonalPatterns, SCRBStats"""


async def save_conversation(
    session_id: str,
    query: str,
    response: str,
    intent: str,
    language: str,
):
    """Save conversation to DataStore for audit trail."""
    datastore = get_catalyst_client()
    if datastore is None:
        return

    try:
        row = {
            "SessionID": session_id,
            "Query": query[:1000],
            "Response": response[:4000],
            "Intent": intent,
            "Language": language,
            "Timestamp": datetime.utcnow().isoformat(),
        }
        datastore.table("Conversations").insert_row(row)
    except Exception as e:
        logger.warning(f"Failed to save conversation: {e}")


@router.post("/query", response_model=ChatResponse)
async def chat_query(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    query = req.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # 1. Detect language
    language = detect_language(query)

    # 2. Classify intent
    intent = classify_intent(query)

    # 3. Query DataStore for relevant data
    data, sources = await query_datastore_for_intent(intent, req.district_filter, query)

    # 4. Build system prompt
    system_prompt = build_system_prompt(intent, data, sources, language)

    # 5. Call Claude API
    response_text = ""
    confidence = "HIGH"

    if not ANTHROPIC_API_KEY:
        # Fallback for local dev without API key
        response_text = _generate_mock_response(intent, data, language, sources)
        confidence = "MEDIUM"
    else:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=system_prompt,
                messages=[{"role": "user", "content": query}],
            )
            response_text = message.content[0].text
            confidence = "HIGH"
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            response_text = _generate_mock_response(intent, data, language, sources)
            confidence = "LOW"

    # 6. Save conversation
    await save_conversation(session_id, query, response_text, intent, language)

    return ChatResponse(
        response=response_text,
        intent=intent,
        language=language,
        sources=sources,
        confidence=confidence,
        session_id=session_id,
    )


def _generate_mock_response(
    intent: str, data: list, language: str, sources: list
) -> str:
    """Fallback response when Claude API is unavailable."""
    source_str = " | ".join(sources)

    if not data:
        base = "No data available for this query in the current DataStore configuration."
    elif intent == "HOTSPOT_QUERY":
        top = data[0] if data else {}
        base = (
            f"Top crime hotspot: {top.get('DistrictName', 'N/A')} with {top.get('crimeCount', 0)} FIRs "
            f"(score: {top.get('score', 0)}). Dominant crime type: {top.get('dominantCrimeType', 'N/A')}."
        )
    elif intent == "ACCUSED_QUERY":
        names = ", ".join(r.get("AccusedName", "Unknown") for r in data[:3])
        base = f"Top repeat offenders: {names}. These individuals appear in multiple FIRs in the system."
    elif intent == "PREDICTION_QUERY":
        top = data[0] if data else {}
        base = (
            f"Highest risk: {top.get('DistrictName', 'N/A')} — {top.get('CrimeType', 'N/A')} "
            f"(risk score: {top.get('RiskScore', 0):.2f}, predicted count: {top.get('PredictedCount', 0)}). "
            f"Factors: {top.get('shap_factors', 'N/A')}."
        )
    else:
        base = f"Queried {len(data)} records from {source_str}. Data loaded successfully."

    return f"{base}\n\nSources: {source_str} | Confidence: MEDIUM\n\n(Note: KAVERI AI engine is running in fallback mode — set ANTHROPIC_API_KEY for full intelligence responses.)"
