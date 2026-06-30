"""
POST /webhook/fir/ingest — accepts new FIR in official KSP CCTNS field names.

CaseMaster schema per KSP ER diagram:
  CrimeNo, CaseCategoryID (FK→CaseCategory), GravityOffenceID (FK→GravityOffence),
  CrimeMajorHeadID (FK→CrimeHead), CrimeMinorHeadID (FK→CrimeSubHead),
  CaseStatusID (FK→CaseStatusMaster), latitude, longitude, BriefFacts
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

logger = logging.getLogger("kaveri.webhook")

router = APIRouter()


class FIRIngestRequest(BaseModel):
    # ── Core CaseMaster fields (official ER diagram) ──────────────────────────
    CrimeNo:           str
    CaseCategoryID:    Optional[int] = 1    # FK→CaseCategory (1=FIR, 3=UDR, 4=PAR, 8=Zero FIR)
    GravityOffenceID:  Optional[int] = None  # FK→GravityOffence (1=Heinous, 2=Serious, 3=Other)
    CrimeMajorHeadID:  Optional[int] = None  # FK→CrimeHead (major crime classification)
    CrimeMinorHeadID:  Optional[int] = None  # FK→CrimeSubHead (minor crime sub-head)
    CaseStatusID:      Optional[int] = 1    # FK→CaseStatusMaster (1=Under Investigation)
    PoliceStationID:   Optional[int] = None  # FK→Unit
    PolicePersonID:    Optional[int] = None  # FK→Employee
    # ── Location / time ───────────────────────────────────────────────────────
    DistrictID:        str
    UnitID:            str
    CrimeDateTime:     str
    IncidentFromDate:  Optional[str] = None
    IncidentToDate:    Optional[str] = None
    latitude:          float
    longitude:         float
    BriefFacts:        str
    # ── Complainant (shortcut — full detail goes in ComplainantDetails) ────────
    ComplainantName:   Optional[str] = None
    ComplainantAge:    Optional[int] = None
    ComplainantGender: Optional[str] = None
    # ── Accused shortcut (full detail goes in Accused table) ──────────────────
    AccusedName:       Optional[str] = None
    AccusedAge:        Optional[int] = None
    # ── Victim shortcut ───────────────────────────────────────────────────────
    VictimName:        Optional[str] = None
    VictimAge:         Optional[int] = None
    VictimGender:      Optional[str] = None
    # ── Investigation ─────────────────────────────────────────────────────────
    IPCSections:              Optional[str]  = None
    ArrestMade:               Optional[bool] = False
    InvestigatingOfficerID:   Optional[str]  = None

    @field_validator("CrimeNo")
    @classmethod
    def crime_no_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("CrimeNo cannot be empty")
        return v.strip()

    @field_validator("BriefFacts")
    @classmethod
    def brief_facts_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("BriefFacts cannot be empty")
        return v.strip()

    @field_validator("latitude")
    @classmethod
    def valid_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError(f"Invalid latitude: {v}")
        return v

    @field_validator("longitude")
    @classmethod
    def valid_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError(f"Invalid longitude: {v}")
        return v


class FIRIngestResponse(BaseModel):
    success:      bool
    CrimeNo:      str
    alerts_fired: list
    message:      str


def _get_datastore():
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


async def _save_fir_to_datastore(fir: FIRIngestRequest) -> bool:
    """Save FIR to CaseMaster table using official ER diagram field names."""
    datastore = _get_datastore()
    if datastore is None:
        logger.info(f"DataStore not configured — FIR {fir.CrimeNo} logged in memory only")
        return True

    try:
        now = datetime.utcnow().isoformat()
        # CaseNo = YYYY + 5-digit serial (last 9 chars of CrimeNo per ER diagram)
        case_no = fir.CrimeNo[-9:] if len(fir.CrimeNo) >= 9 else fir.CrimeNo

        row = {
            "CrimeNo":           fir.CrimeNo,
            "CaseNo":            case_no,
            "CrimeRegisteredDate": now,
            "PoliceStationID":   fir.PoliceStationID or 1,
            "PolicePersonID":    fir.PolicePersonID  or 1,
            "CaseCategoryID":    fir.CaseCategoryID  or 1,
            "GravityOffenceID":  fir.GravityOffenceID,
            "CrimeMajorHeadID":  fir.CrimeMajorHeadID,
            "CrimeMinorHeadID":  fir.CrimeMinorHeadID,
            "CaseStatusID":      fir.CaseStatusID    or 1,
            "DistrictID":        fir.DistrictID,
            "UnitID":            fir.UnitID,
            "latitude":          fir.latitude,
            "longitude":         fir.longitude,
            "BriefFacts":        fir.BriefFacts,
            "IncidentFromDate":  fir.IncidentFromDate or fir.CrimeDateTime,
            "IncidentToDate":    fir.IncidentToDate   or fir.CrimeDateTime,
            "InfoReceivedPSDate": now,
            "IngestedAt":        now,
        }
        datastore.table("CaseMaster").insert_row(row)
        logger.info(f"FIR {fir.CrimeNo} saved to CaseMaster")
        return True
    except Exception as e:
        logger.error(f"Failed to save FIR {fir.CrimeNo}: {e}")
        return False


async def _broadcast_new_fir(fir: FIRIngestRequest):
    """Broadcast new FIR to all WebSocket clients."""
    try:
        from app import ws_manager
        await ws_manager.broadcast({
            "type": "new_fir",
            "data": {
                "CrimeNo":          fir.CrimeNo,
                "DistrictID":       fir.DistrictID,
                "CrimeMajorHeadID": fir.CrimeMajorHeadID,
                "CrimeMinorHeadID": fir.CrimeMinorHeadID,
                "GravityOffenceID": fir.GravityOffenceID,
                "latitude":         fir.latitude,
                "longitude":        fir.longitude,
                "CrimeDateTime":    fir.CrimeDateTime,
                "BriefFacts":       fir.BriefFacts[:200],
            },
        })
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed: {e}")


@router.post("/fir/ingest", response_model=FIRIngestResponse)
async def ingest_fir(fir: FIRIngestRequest):
    """
    Ingest a new FIR in KSP CCTNS format.
    Accepts official ER diagram field names:
      CrimeNo, CaseCategoryID, GravityOffenceID, CrimeMajorHeadID, CrimeMinorHeadID
    """
    logger.info(
        f"Ingesting FIR: {fir.CrimeNo} | District: {fir.DistrictID} | "
        f"MajorHead: {fir.CrimeMajorHeadID} | MinorHead: {fir.CrimeMinorHeadID}"
    )

    saved = await _save_fir_to_datastore(fir)
    if not saved:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist FIR {fir.CrimeNo} to DataStore",
        )

    from alerts.alert_engine import check_alerts
    fir_dict = fir.model_dump()
    alerts_fired = await check_alerts(fir_dict)

    await _broadcast_new_fir(fir)

    serializable_alerts = [
        {
            "AlertType":   a.get("AlertType"),
            "Severity":    a.get("Severity"),
            "Description": a.get("Description"),
            "AlertID":     a.get("AlertID"),
        }
        for a in alerts_fired
    ]

    return FIRIngestResponse(
        success=True,
        CrimeNo=fir.CrimeNo,
        alerts_fired=serializable_alerts,
        message=f"FIR {fir.CrimeNo} ingested. {len(alerts_fired)} alert(s) fired.",
    )
