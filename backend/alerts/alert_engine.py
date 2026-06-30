import logging
import math
import asyncio
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger("kaveri.alerts")

# In-memory alert store (fallback when DataStore not configured)
_alert_store: list = []
_alert_id_counter = 1


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two GPS coordinates using Haversine formula."""
    R = 6371.0  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _get_datastore():
    """Get Catalyst DataStore client or None."""
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


def _query_recent_firs(
    datastore,
    district_id: str,
    crime_minor_head_id,
    hours: int,
) -> list:
    """Count recent FIRs by district + CrimeMinorHeadID in past N hours."""
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    if datastore is None:
        return _alert_store

    try:
        zcql = (
            f"SELECT CrimeNo, latitude, longitude, IncidentFromDate FROM CaseMaster "
            f"WHERE DistrictID = '{district_id}' "
            f"AND CrimeMinorHeadID = {crime_minor_head_id!r} "
            f"AND IncidentFromDate >= '{since}'"
        )
        result = datastore.execute_query(zcql)
        return result.get("data", [])
    except Exception as e:
        logger.warning(f"DataStore query failed: {e}")
        return []


def _query_nearby_firs(
    datastore,
    lat: float,
    lng: float,
    hours: int,
) -> list:
    """Find FIRs within a broad bounding box (pre-filter before Haversine)."""
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    # ~2km bounding box: 1 degree lat ~ 111 km, 1 degree lng ~ 91 km at Karnataka latitude
    lat_delta = 2.0 / 111.0
    lng_delta = 2.0 / 91.0

    if datastore is None:
        return []

    try:
        zcql = (
            f"SELECT CrimeNo, latitude, longitude, IncidentFromDate FROM CaseMaster "
            f"WHERE latitude BETWEEN {lat - lat_delta} AND {lat + lat_delta} "
            f"AND longitude BETWEEN {lng - lng_delta} AND {lng + lng_delta} "
            f"AND IncidentFromDate >= '{since}'"
        )
        result = datastore.execute_query(zcql)
        return result.get("data", [])
    except Exception as e:
        logger.warning(f"Nearby FIR query failed: {e}")
        return []


def _query_repeat_accused(datastore, accused_name: str) -> list:
    """Check if accused name already exists in Accused table."""
    if not accused_name:
        return []

    if datastore is None:
        return []

    try:
        safe_name = accused_name.replace("'", "''")
        zcql = (
            f"SELECT AccusedName, CaseMasterID FROM Accused "
            f"WHERE AccusedName = '{safe_name}'"
        )
        result = datastore.execute_query(zcql)
        return result.get("data", [])
    except Exception as e:
        logger.warning(f"Repeat accused query failed: {e}")
        return []


def _save_alert(datastore, alert: dict) -> str:
    """Persist alert to DataStore Alerts table. Returns alert ID."""
    global _alert_id_counter, _alert_store

    if datastore is None:
        alert_id = str(_alert_id_counter)
        _alert_id_counter += 1
        alert_copy = dict(alert)
        alert_copy["AlertID"] = alert_id
        alert_copy["Acknowledged"] = False
        _alert_store.append(alert_copy)
        return alert_id

    try:
        row = {
            "AlertType": alert["AlertType"],
            "Severity": alert["Severity"],
            "Description": alert["Description"],
            "CrimeNo": alert.get("CrimeNo", ""),
            "DistrictID": alert.get("DistrictID", ""),
            "Timestamp": alert.get("timestamp", datetime.utcnow().isoformat()),
            "Acknowledged": False,
        }
        result = datastore.table("Alerts").insert_row(row)
        return str(result.get("ROWID", ""))
    except Exception as e:
        logger.error(f"Failed to save alert: {e}")
        return ""


async def _broadcast_alert(alert: dict):
    """Broadcast alert to all connected WebSocket clients."""
    try:
        from app import ws_manager
        await ws_manager.broadcast({
            "type": "alert",
            "data": alert,
        })
    except Exception as e:
        logger.warning(f"WebSocket broadcast failed: {e}")


async def check_alerts(fir_data: dict) -> list:
    """
    Check all alert rules against an incoming FIR.

    Args:
        fir_data: Validated FIR dict with fields: CrimeNo, CrimeSubHeadID,
                  DistrictID, GravityOffenceID, Latitude, Longitude,
                  CrimeDateTime, AccusedName (optional).

    Returns:
        List of fired alert dicts.
    """
    fired_alerts = []
    datastore = _get_datastore()

    crime_no          = fir_data.get("CrimeNo", "UNKNOWN")
    district_id       = fir_data.get("DistrictID", "")
    # Use official ER diagram field names; fall back to legacy CrimeSubHeadID for compat
    crime_minor_head_id = fir_data.get("CrimeMinorHeadID") or fir_data.get("CrimeSubHeadID", "")
    gravity_id        = fir_data.get("GravityOffenceID")
    lat = float(fir_data.get("Latitude", 0) or 0)
    lng = float(fir_data.get("Longitude", 0) or 0)
    accused_name = fir_data.get("AccusedName", "")
    timestamp = datetime.utcnow().isoformat()

    # --- Rule 1: HEINOUS_OFFENCE ---
    # GravityOffenceID == 1 means murder/rape/heinous crime
    try:
        gravity_val = int(gravity_id) if gravity_id is not None else -1
    except (TypeError, ValueError):
        gravity_val = -1

    if gravity_val == 1:
        alert = {
            "AlertType": "HEINOUS_OFFENCE",
            "Severity": "CRITICAL",
            "Description": (
                f"Heinous offence registered: FIR {crime_no} in district {district_id}. "
                f"Immediate senior officer notification required."
            ),
            "CrimeNo": crime_no,
            "DistrictID": district_id,
            "timestamp": timestamp,
        }
        alert_id = _save_alert(datastore, alert)
        alert["AlertID"] = alert_id
        fired_alerts.append(alert)
        await _broadcast_alert(alert)
        logger.info(f"HEINOUS_OFFENCE alert fired for {crime_no}")

    # --- Rule 2: CRIME_SPIKE ---
    # 5+ FIRs of same crime type in same district within 8 hours
    recent_same = _query_recent_firs(datastore, district_id, crime_minor_head_id, hours=8)
    # +1 to include current FIR
    if len(recent_same) + 1 >= 5:
        alert = {
            "AlertType": "CRIME_SPIKE",
            "Severity": "HIGH",
            "Description": (
                f"Crime spike detected: {len(recent_same) + 1} FIRs of CrimeMinorHeadID={crime_minor_head_id} "
                f"in district {district_id} within the last 8 hours. Latest: {crime_no}."
            ),
            "CrimeNo": crime_no,
            "DistrictID": district_id,
            "timestamp": timestamp,
        }
        alert_id = _save_alert(datastore, alert)
        alert["AlertID"] = alert_id
        fired_alerts.append(alert)
        await _broadcast_alert(alert)
        logger.info(f"CRIME_SPIKE alert fired for {district_id}/CrimeMinorHead={crime_minor_head_id}")

    # --- Rule 3: CLUSTER_ALERT ---
    # 3+ FIRs within ~2km radius in last 4 hours
    if lat and lng:
        nearby = _query_nearby_firs(datastore, lat, lng, hours=4)
        # Filter by actual Haversine distance <= 2km
        close_firs = [
            f for f in nearby
            if (
                f.get("latitude") is not None
                and f.get("longitude") is not None
                and _haversine_km(
                    lat, lng,
                    float(f["latitude"]), float(f["longitude"])
                ) <= 2.0
            )
        ]
        # +1 for current FIR
        if len(close_firs) + 1 >= 3:
            alert = {
                "AlertType": "CLUSTER_ALERT",
                "Severity": "HIGH",
                "Description": (
                    f"Crime cluster detected: {len(close_firs) + 1} FIRs within 2km of "
                    f"{lat:.4f},{lng:.4f} in the last 4 hours. District: {district_id}. "
                    f"Latest FIR: {crime_no}."
                ),
                "CrimeNo": crime_no,
                "DistrictID": district_id,
                "timestamp": timestamp,
            }
            alert_id = _save_alert(datastore, alert)
            alert["AlertID"] = alert_id
            fired_alerts.append(alert)
            await _broadcast_alert(alert)
            logger.info(f"CLUSTER_ALERT fired near {lat},{lng}")

    # --- Rule 4: REPEAT_ACCUSED ---
    # AccusedName in new FIR matches existing records
    if accused_name and accused_name.strip():
        existing = _query_repeat_accused(datastore, accused_name.strip())
        if existing:
            case_ids = [str(r.get("CaseMasterID", "?")) for r in existing[:3]]
            alert = {
                "AlertType": "REPEAT_ACCUSED",
                "Severity": "CRITICAL",
                "Description": (
                    f"Repeat accused detected: '{accused_name}' already appears in "
                    f"{len(existing)} previous FIR(s) (cases: {', '.join(case_ids)}). "
                    f"New FIR: {crime_no}."
                ),
                "CrimeNo": crime_no,
                "DistrictID": district_id,
                "timestamp": timestamp,
                "AccusedName": accused_name,
            }
            alert_id = _save_alert(datastore, alert)
            alert["AlertID"] = alert_id
            fired_alerts.append(alert)
            await _broadcast_alert(alert)
            logger.info(f"REPEAT_ACCUSED alert fired for {accused_name}")

    return fired_alerts
