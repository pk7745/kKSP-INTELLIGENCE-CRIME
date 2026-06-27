import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger("kaveri.hotspots")

router = APIRouter()

_MOCK_HOTSPOTS = [
    {
        "DistrictID": "BEU",
        "DistrictName": "Bengaluru Urban",
        "lat": 12.9716,
        "lng": 77.5946,
        "score": 92,
        "crimeCount": 1247,
        "dominantCrimeType": "Theft",
        "lastUpdated": "2026-01-15T12:00:00",
    },
    {
        "DistrictID": "MYS",
        "DistrictName": "Mysuru",
        "lat": 12.2958,
        "lng": 76.6394,
        "score": 71,
        "crimeCount": 634,
        "dominantCrimeType": "Robbery",
        "lastUpdated": "2026-01-15T12:00:00",
    },
    {
        "DistrictID": "KLB",
        "DistrictName": "Kalaburagi",
        "lat": 17.3297,
        "lng": 76.8200,
        "score": 68,
        "crimeCount": 521,
        "dominantCrimeType": "Murder",
        "lastUpdated": "2026-01-15T12:00:00",
    },
    {
        "DistrictID": "BMR",
        "DistrictName": "Bengaluru Rural",
        "lat": 13.0827,
        "lng": 77.5970,
        "score": 58,
        "crimeCount": 312,
        "dominantCrimeType": "Theft",
        "lastUpdated": "2026-01-15T12:00:00",
    },
    {
        "DistrictID": "BLR",
        "DistrictName": "Belagavi",
        "lat": 15.8497,
        "lng": 74.4977,
        "score": 55,
        "crimeCount": 298,
        "dominantCrimeType": "Robbery",
        "lastUpdated": "2026-01-15T12:00:00",
    },
    {
        "DistrictID": "DKN",
        "DistrictName": "Dakshina Kannada",
        "lat": 12.8698,
        "lng": 74.8431,
        "score": 44,
        "crimeCount": 187,
        "dominantCrimeType": "Cyber Crime",
        "lastUpdated": "2026-01-15T12:00:00",
    },
    {
        "DistrictID": "HVR",
        "DistrictName": "Haveri",
        "lat": 14.7957,
        "lng": 75.3996,
        "score": 38,
        "crimeCount": 143,
        "dominantCrimeType": "Assault",
        "lastUpdated": "2026-01-15T12:00:00",
    },
    {
        "DistrictID": "BGT",
        "DistrictName": "Bagalkot",
        "lat": 16.1691,
        "lng": 75.6964,
        "score": 35,
        "crimeCount": 127,
        "dominantCrimeType": "Theft",
        "lastUpdated": "2026-01-15T12:00:00",
    },
]


def _get_datastore():
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


@router.get("")
async def get_hotspots():
    """
    Return current hotspot data from Hotspots table (refreshed every 5 min by Cron).
    Each hotspot includes district, GPS coordinates, crime score, count, and dominant type.
    """
    datastore = _get_datastore()

    if datastore is None:
        return {"hotspots": _MOCK_HOTSPOTS, "source": "memory", "count": len(_MOCK_HOTSPOTS)}

    try:
        zcql = (
            "SELECT DistrictID, DistrictName, lat, lng, score, crimeCount, "
            "dominantCrimeType, lastUpdated FROM Hotspots ORDER BY score DESC"
        )
        result = datastore.execute_query(zcql)
        hotspots = result.get("data", [])

        if not hotspots:
            # Hotspot table empty — return mock data until Cron populates it
            return {
                "hotspots": _MOCK_HOTSPOTS,
                "source": "memory_fallback",
                "count": len(_MOCK_HOTSPOTS),
            }

        return {"hotspots": hotspots, "source": "datastore", "count": len(hotspots)}

    except Exception as e:
        logger.error(f"Hotspot query failed: {e}")
        # Return mock data on error rather than 500
        return {
            "hotspots": _MOCK_HOTSPOTS,
            "source": "memory_error_fallback",
            "count": len(_MOCK_HOTSPOTS),
            "error": str(e),
        }
