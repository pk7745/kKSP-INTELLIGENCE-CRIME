import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter

logger = logging.getLogger("kaveri.simulator")

router = APIRouter()

# Streamer state
_streamer_task: Optional[asyncio.Task] = None
_running = False

# Seeded FIR templates — field names per official KSP ER diagram
# CrimeMajorHeadID → FK→CrimeHead, CrimeMinorHeadID → FK→CrimeSubHead
# GravityOffenceID: 1=Heinous, 2=Serious, 3=Other Cognizable
_FIR_TEMPLATES = [
    {
        "CrimeMajorHeadID": 2, "CrimeMinorHeadID": 5,   # Crimes Against Property / Theft
        "GravityOffenceID": 3, "CaseCategoryID": 1,
        "DistrictID": "BEU", "UnitID": "0001",
        "latitude": 12.9716, "longitude": 77.5946,
        "BriefFacts": "Theft of two-wheeler from parking lot near IT park.",
    },
    {
        "CrimeMajorHeadID": 2, "CrimeMinorHeadID": 6,   # Crimes Against Property / Robbery
        "GravityOffenceID": 2, "CaseCategoryID": 1,
        "DistrictID": "MYS", "UnitID": "0001",
        "latitude": 12.2958, "longitude": 76.6394,
        "BriefFacts": "Chain snatching near Chamundi Hills bus stop. Accused fled on motorcycle.",
        "AccusedName": "Suresh Naik",
    },
    {
        "CrimeMajorHeadID": 1, "CrimeMinorHeadID": 1,   # Crimes Against Body / Murder
        "GravityOffenceID": 1, "CaseCategoryID": 1,
        "DistrictID": "KLB", "UnitID": "0001",
        "latitude": 17.3297, "longitude": 76.8200,
        "BriefFacts": "Suspected homicide — body found near canal. Land dispute motive suspected.",
    },
    {
        "CrimeMajorHeadID": 5, "CrimeMinorHeadID": 16,  # Cyber Crimes / Cyber Fraud
        "GravityOffenceID": 3, "CaseCategoryID": 1,
        "DistrictID": "DKS", "UnitID": "0001",
        "latitude": 12.8698, "longitude": 74.8431,
        "BriefFacts": "Online fraud — victim deceived into transferring Rs 2.5 lakhs via UPI.",
    },
    {
        "CrimeMajorHeadID": 1, "CrimeMinorHeadID": 4,   # Crimes Against Body / Assault
        "GravityOffenceID": 2, "CaseCategoryID": 1,
        "DistrictID": "BLG", "UnitID": "0001",
        "latitude": 15.8497, "longitude": 74.4977,
        "BriefFacts": "Physical assault during property dispute. Victim hospitalised with injuries.",
    },
    {
        "CrimeMajorHeadID": 2, "CrimeMinorHeadID": 8,   # Crimes Against Property / Burglary
        "GravityOffenceID": 3, "CaseCategoryID": 1,
        "DistrictID": "BMR", "UnitID": "0001",
        "latitude": 13.0827, "longitude": 77.5970,
        "BriefFacts": "House burglary during daytime — valuables and electronics stolen.",
    },
    {
        "CrimeMajorHeadID": 2, "CrimeMinorHeadID": 6,   # Crimes Against Property / Robbery
        "GravityOffenceID": 1, "CaseCategoryID": 1,
        "DistrictID": "BEU", "UnitID": "0002",
        "latitude": 12.9352, "longitude": 77.6245,
        "BriefFacts": "Armed robbery at ATM vestibule. Two accused, one arrested at scene.",
        "AccusedName": "Ravi Kumar",
    },
    {
        "CrimeMajorHeadID": 3, "CrimeMinorHeadID": 11,  # Crimes Against Women / Molestation
        "GravityOffenceID": 2, "CaseCategoryID": 1,
        "DistrictID": "MYS", "UnitID": "0002",
        "latitude": 12.3051, "longitude": 76.6552,
        "BriefFacts": "Eve-teasing and molestation reported near college campus. Victim filed complaint.",
    },
]

_serial_counters: dict = {}


def _generate_crime_no(district_id: str, unit_id: str = "0001") -> str:
    """
    Generate sequential CrimeNo in official KSP CCTNS format per ER diagram:
    1-digit CaseCategoryCode + 4-digit DistrictID + 4-digit PoliceStationID + 4-digit Year + 5-digit Serial
    Example: 104430006202600001
    """
    year = datetime.utcnow().year
    if district_id not in _serial_counters:
        _serial_counters[district_id] = random.randint(500, 999)
    _serial_counters[district_id] += 1
    serial       = _serial_counters[district_id]
    dist_part    = district_id[:4].ljust(4, "0")
    station_part = unit_id[:4].ljust(4, "0")
    return f"1{dist_part}{station_part}{year}{serial:05d}"


def _add_gps_noise(lat: float, lng: float, radius_km: float = 0.5) -> tuple:
    """Add slight random offset to GPS coordinates for realism."""
    # 0.01 degrees ~= 1.1 km
    delta = radius_km * 0.009
    return (
        lat + random.uniform(-delta, delta),
        lng + random.uniform(-delta, delta),
    )


async def _stream_single_event():
    """Pick a random FIR template and ingest it via the webhook endpoint."""
    template = random.choice(_FIR_TEMPLATES)
    crime_no = _generate_crime_no(template["DistrictID"], template.get("UnitID", "0001"))
    lat, lng = _add_gps_noise(template["latitude"], template["longitude"])

    fir_data = {
        "CrimeNo":          crime_no,
        "CaseCategoryID":   template.get("CaseCategoryID", 1),
        "GravityOffenceID": template.get("GravityOffenceID"),
        "CrimeMajorHeadID": template.get("CrimeMajorHeadID"),
        "CrimeMinorHeadID": template.get("CrimeMinorHeadID"),
        "CaseStatusID":     1,
        "DistrictID":       template["DistrictID"],
        "UnitID":           template["UnitID"],
        "CrimeDateTime":    datetime.utcnow().isoformat(),
        "latitude":         round(lat, 6),
        "longitude":        round(lng, 6),
        "BriefFacts":       template["BriefFacts"],
        "AccusedName":      template.get("AccusedName"),
    }

    try:
        # Call the webhook ingest function directly (avoid HTTP round-trip)
        from api.webhook import ingest_fir, FIRIngestRequest
        fir_request = FIRIngestRequest(**fir_data)
        result = await ingest_fir(fir_request)
        logger.info(
            f"Simulator: Streamed FIR {crime_no} | "
            f"District: {template['DistrictID']} | "
            f"Alerts: {len(result.alerts_fired)}"
        )
        return result
    except Exception as e:
        logger.error(f"Simulator event stream error: {e}")
        # Broadcast directly on error
        try:
            from app import ws_manager
            await ws_manager.broadcast({
                "type": "new_fir",
                "data": fir_data,
            })
        except Exception:
            pass


async def _run_streamer(interval_seconds: int):
    """Background loop that streams simulated FIR events at regular intervals."""
    global _running
    logger.info(f"Event streamer started (interval: {interval_seconds}s)")
    while _running:
        await _stream_single_event()
        await asyncio.sleep(interval_seconds)
    logger.info("Event streamer stopped")


def stream_events(interval_seconds: int = 30):
    """
    Start the event streamer as a background asyncio task.
    Replays seeded FIR templates as live events at the given interval.
    """
    global _streamer_task, _running
    if _running:
        logger.warning("Streamer already running")
        return

    _running = True
    loop = asyncio.get_event_loop()
    _streamer_task = loop.create_task(_run_streamer(interval_seconds))


def stop_events():
    """Stop the event streamer."""
    global _streamer_task, _running
    _running = False
    if _streamer_task and not _streamer_task.done():
        _streamer_task.cancel()
        _streamer_task = None
    logger.info("Event streamer stop requested")


@router.get("/simulator/start")
async def start_simulator(interval: int = 30):
    """Start the FIR event simulator. Events are broadcast to all WebSocket clients."""
    global _running
    if _running:
        return {"status": "already_running", "interval_seconds": interval}
    stream_events(interval_seconds=interval)
    return {
        "status": "started",
        "interval_seconds": interval,
        "message": f"Simulator will generate a new FIR event every {interval} seconds.",
    }


@router.get("/simulator/stop")
async def stop_simulator():
    """Stop the FIR event simulator."""
    global _running
    if not _running:
        return {"status": "not_running"}
    stop_events()
    return {"status": "stopped", "message": "Event simulator stopped."}


@router.get("/simulator/status")
async def simulator_status():
    """Return the current status of the event simulator."""
    return {
        "running": _running,
        "task_pending": _streamer_task is not None and not (_streamer_task.done() if _streamer_task else True),
    }


@router.post("/simulator/fire")
async def fire_single_event():
    """Manually fire a single simulated FIR event."""
    result = await _stream_single_event()
    if result:
        return {
            "status": "fired",
            "CrimeNo": result.CrimeNo,
            "alerts_fired": result.alerts_fired,
        }
    return {"status": "fired", "message": "Event sent to WebSocket clients"}
