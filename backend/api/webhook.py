import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator

logger = logging.getLogger("kaveri.webhook")

router = APIRouter()


class FIRIngestRequest(BaseModel):
    CrimeNo: str
    CrimeSubHeadID: str
    DistrictID: str
    UnitID: str
    CrimeDateTime: str
    Latitude: float
    Longitude: float
    BriefFacts: str
    # Optional but common KSP CCTNS fields
    GravityOffenceID: Optional[int] = None
    CaseCategory: Optional[str] = None
    ComplainantName: Optional[str] = None
    ComplainantAge: Optional[int] = None
    ComplainantGender: Optional[str] = None
    AccusedName: Optional[str] = None
    AccusedAge: Optional[int] = None
    VictimName: Optional[str] = None
    VictimAge: Optional[int] = None
    VictimGender: Optional[str] = None
    IPCSections: Optional[str] = None
    ArrestMade: Optional[bool] = False
    InvestigatingOfficerID: Optional[str] = None

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

    @field_validator("Latitude")
    @classmethod
    def valid_latitude(cls, v: float) -> float:
        if not (-90 <= v <= 90):
            raise ValueError(f"Invalid latitude: {v}")
        return v

    @field_validator("Longitude")
    @classmethod
    def valid_longitude(cls, v: float) -> float:
        if not (-180 <= v <= 180):
            raise ValueError(f"Invalid longitude: {v}")
        return v


class FIRIngestResponse(BaseModel):
    success: bool
    CrimeNo: str
    alerts_fired: list
    message: str


def _get_datastore():
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


async def _save_fir_to_datastore(fir: FIRIngestRequest) -> bool:
    """Save FIR to CaseMaster table in Catalyst DataStore."""
    datastore = _get_datastore()
    if datastore is None:
        logger.info(f"DataStore not configured — FIR {fir.CrimeNo} logged in memory only")
        return True

    try:
        row = {
            "CrimeNo": fir.CrimeNo,
            "CrimeSubHeadID": fir.CrimeSubHeadID,
            "DistrictID": fir.DistrictID,
            "UnitID": fir.UnitID,
            "CrimeDateTime": fir.CrimeDateTime,
            "Latitude": fir.Latitude,
            "Longitude": fir.Longitude,
            "BriefFacts": fir.BriefFacts,
            "GravityOffenceID": fir.GravityOffenceID,
            "CaseCategory": fir.CaseCategory or "R",
            "InvestigatingOfficerID": fir.InvestigatingOfficerID or "",
            "IngestedAt": datetime.utcnow().isoformat(),
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
                "CrimeNo": fir.CrimeNo,
                "DistrictID": fir.DistrictID,
                "CrimeSubHeadID": fir.CrimeSubHeadID,
                "Latitude": fir.Latitude,
                "Longitude": fir.Longitude,
                "CrimeDateTime": fir.CrimeDateTime,
                "BriefFacts": fir.BriefFacts[:200],
            },
        })
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed: {e}")


@router.post("/fir/ingest", response_model=FIRIngestResponse)
async def ingest_fir(fir: FIRIngestRequest):
    """
    Ingest a new FIR in KSP CCTNS format.

    This endpoint accepts FIRs from:
    - KSP CCTNS production system (live police stations)
    - KAVERI demo simulator ("Simulate New Crime" button)
    """
    logger.info(f"Ingesting FIR: {fir.CrimeNo} | District: {fir.DistrictID}")

    # 1. Persist to DataStore
    saved = await _save_fir_to_datastore(fir)
    if not saved:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to persist FIR {fir.CrimeNo} to DataStore",
        )

    # 2. Run alert engine
    from alerts.alert_engine import check_alerts
    fir_dict = fir.model_dump()
    alerts_fired = await check_alerts(fir_dict)

    # 3. Broadcast new FIR event to WebSocket clients
    await _broadcast_new_fir(fir)

    # 4. Serialize alerts for response (remove non-serializable fields)
    serializable_alerts = []
    for alert in alerts_fired:
        serializable_alerts.append({
            "AlertType": alert.get("AlertType"),
            "Severity": alert.get("Severity"),
            "Description": alert.get("Description"),
            "AlertID": alert.get("AlertID"),
        })

    return FIRIngestResponse(
        success=True,
        CrimeNo=fir.CrimeNo,
        alerts_fired=serializable_alerts,
        message=f"FIR {fir.CrimeNo} ingested successfully. {len(alerts_fired)} alert(s) fired.",
    )
