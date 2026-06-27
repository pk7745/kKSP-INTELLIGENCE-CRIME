import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger("kaveri.predictions")

router = APIRouter()

_MOCK_PREDICTIONS = [
    {
        "DistrictID": "BEU",
        "DistrictName": "Bengaluru Urban",
        "CrimeType": "Theft",
        "RiskScore": 0.89,
        "PredictedCount": 145,
        "date": "2026-01-22",
        "shap_factors": "Festival season (+0.31), High footfall (+0.28), Weekend (+0.18)",
    },
    {
        "DistrictID": "BEU",
        "DistrictName": "Bengaluru Urban",
        "CrimeType": "Robbery",
        "RiskScore": 0.76,
        "PredictedCount": 42,
        "date": "2026-01-22",
        "shap_factors": "Night hours (+0.25), Low patrol density (+0.22), Past trend (+0.19)",
    },
    {
        "DistrictID": "MYS",
        "DistrictName": "Mysuru",
        "CrimeType": "Robbery",
        "RiskScore": 0.74,
        "PredictedCount": 28,
        "date": "2026-01-22",
        "shap_factors": "Weekend (+0.29), Tourist season (+0.24), Low lighting (+0.12)",
    },
    {
        "DistrictID": "KLB",
        "DistrictName": "Kalaburagi",
        "CrimeType": "Murder",
        "RiskScore": 0.67,
        "PredictedCount": 3,
        "date": "2026-01-22",
        "shap_factors": "Land dispute (+0.38), Alcohol access (+0.21), Past incidents (+0.15)",
    },
    {
        "DistrictID": "BEU",
        "DistrictName": "Bengaluru Urban",
        "CrimeType": "Cyber Crime",
        "RiskScore": 0.65,
        "PredictedCount": 67,
        "date": "2026-01-23",
        "shap_factors": "Digital payment festival offers (+0.34), New Year scams (+0.22)",
    },
    {
        "DistrictID": "BMR",
        "DistrictName": "Bengaluru Rural",
        "CrimeType": "Theft",
        "RiskScore": 0.58,
        "PredictedCount": 31,
        "date": "2026-01-23",
        "shap_factors": "Highway traffic (+0.27), Low patrol (+0.20), Night hours (+0.15)",
    },
    {
        "DistrictID": "BLR",
        "DistrictName": "Belagavi",
        "CrimeType": "Assault",
        "RiskScore": 0.52,
        "PredictedCount": 18,
        "date": "2026-01-24",
        "shap_factors": "Political rally scheduled (+0.31), Alcohol (+0.18)",
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
async def get_predictions(
    district_id: Optional[str] = Query(None, description="Filter by DistrictID"),
):
    """
    Return 7-day crime risk predictions from XGBoost model output.
    Predictions are loaded by train_predict.py and refreshed every 30 min by Cron.
    """
    datastore = _get_datastore()

    if datastore is None:
        predictions = _MOCK_PREDICTIONS
        if district_id:
            predictions = [p for p in predictions if p["DistrictID"] == district_id]
        return {
            "predictions": predictions,
            "source": "memory",
            "count": len(predictions),
        }

    try:
        district_clause = f"AND DistrictID = '{district_id}'" if district_id else ""
        zcql = (
            f"SELECT DistrictID, DistrictName, CrimeType, RiskScore, "
            f"PredictedCount, date, shap_factors FROM Predictions "
            f"WHERE 1=1 {district_clause} "
            f"ORDER BY RiskScore DESC LIMIT 50"
        )
        result = datastore.execute_query(zcql)
        predictions = result.get("data", [])

        if not predictions:
            # Predictions not yet loaded — return mock until model runs
            mock = _MOCK_PREDICTIONS
            if district_id:
                mock = [p for p in mock if p["DistrictID"] == district_id]
            return {
                "predictions": mock,
                "source": "memory_fallback",
                "count": len(mock),
            }

        return {
            "predictions": predictions,
            "source": "datastore",
            "count": len(predictions),
        }

    except Exception as e:
        logger.error(f"Predictions query failed: {e}")
        mock = _MOCK_PREDICTIONS
        if district_id:
            mock = [p for p in mock if p["DistrictID"] == district_id]
        return {
            "predictions": mock,
            "source": "memory_error_fallback",
            "count": len(mock),
            "error": str(e),
        }
