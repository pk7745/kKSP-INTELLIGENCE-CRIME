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

# Seeded FIR templates for realistic simulation
_FIR_TEMPLATES = [
    {
        "CrimeSubHeadID": "THEFT",
        "DistrictID": "BEU",
        "UnitID": "BEU0001",
        "Latitude": 12.9716,
        "Longitude": 77.5946,
        "BriefFacts": "Theft of two-wheeler from parking lot near IT park.",
        "GravityOffenceID": 3,
    },
    {
        "CrimeSubHeadID": "ROBBERY",
        "DistrictID": "MYS",
        "UnitID": "MYS0001",
        "Latitude": 12.2958,
        "Longitude": 76.6394,
        "BriefFacts": "Chain snatching near Chamundi Hills bus stop. Accused fled on motorcycle.",
        "GravityOffenceID": 2,
        "AccusedName": "Suresh Naik",
    },
    {
        "CrimeSubHeadID": "MURDER",
        "DistrictID": "KLB",
        "UnitID": "KLB0001",
        "Latitude": 17.3297,
        "Longitude": 76.8200,
        "BriefFacts": "Suspected homicide — body found near canal. Land dispute motive suspected.",
        "GravityOffenceID": 1,
    },
    {
        "CrimeSubHeadID": "CYBER_CRIME",
        "DistrictID": "DKN",
        "UnitID": "DKN0001",
        "Latitude": 12.8698,
        "Longitude": 74.8431,
        "BriefFacts": "Online fraud — victim deceived into transferring Rs 2.5 lakhs via UPI.",
        "GravityOffenceID": 3,
    },
    {
        "CrimeSubHeadID": "ASSAULT",
        "DistrictID": "BLR",
        "UnitID": "BLR0001",
        "Latitude": 15.8497,
        "Longitude": 74.4977,
        "BriefFacts": "Physical assault during property dispute. Victim hospitalised with injuries.",
        "GravityOffenceID": 2,
    },
    {
        "CrimeSubHeadID": "THEFT",
        "DistrictID": "BMR",
        "UnitID": "BMR0001",
        "Latitude": 13.0827,
        "Longitude": 77.5970,
        "BriefFacts": "House burglary during daytime — valuables and electronics stolen.",
        "GravityOffenceID": 3,
    },
    {
        "CrimeSubHeadID": "ROBBERY",
        "DistrictID": "BEU",
        "UnitID": "BEU0002",
        "Latitude": 12.9352,
        "Longitude": 77.6245,
        "BriefFacts": "Armed robbery at ATM vestibule. Two accused, one arrested at scene.",
        "GravityOffenceID": 1,
        "AccusedName": "Ravi Kumar",
    },
    {
        "CrimeSubHeadID": "EVE_TEAS",
        "DistrictID": "MYS",
        "UnitID": "MYS0002",
        "Latitude": 12.3051,
        "Longitude": 76.6552,
        "BriefFacts": "Eve-teasing reported near college campus. Victim filed complaint.",
        "GravityOffenceID": 2,
    },
]

_serial_counters: dict = {}


def _generate_crime_no(district_id: str) -> str:
    """Generate a sequential CrimeNo in KSP CCTNS format."""
    year = datetime.utcnow().year
    if district_id not in _serial_counters:
        _serial_counters[district_id] = random.randint(500, 999)
    _serial_counters[district_id] += 1
    serial = _serial_counters[district_id]
    # Format: CaseCategoryCode(1) + DistrictID padded + StationID padded + Year + Serial
    # Simplified for demo
    district_code = district_id[:3].upper().ljust(3, "0")
    return f"1{district_code}0001{year}{serial:05d}"


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
    crime_no = _generate_crime_no(template["DistrictID"])
    lat, lng = _add_gps_noise(template["Latitude"], template["Longitude"])

    fir_data = {
        "CrimeNo": crime_no,
        "CrimeSubHeadID": template["CrimeSubHeadID"],
        "DistrictID": template["DistrictID"],
        "UnitID": template["UnitID"],
        "CrimeDateTime": datetime.utcnow().isoformat(),
        "Latitude": round(lat, 6),
        "Longitude": round(lng, 6),
        "BriefFacts": template["BriefFacts"],
        "GravityOffenceID": template.get("GravityOffenceID"),
        "AccusedName": template.get("AccusedName"),
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
