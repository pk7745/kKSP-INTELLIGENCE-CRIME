import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("kaveri.alerts")

router = APIRouter()


def _get_datastore():
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


@router.get("")
async def get_alerts():
    """Return the 50 most recent alerts from the Alerts table."""
    datastore = _get_datastore()

    if datastore is None:
        # Return from in-memory alert store
        from alerts.alert_engine import _alert_store
        recent = sorted(_alert_store, key=lambda x: x.get("timestamp", ""), reverse=True)[:50]
        return {"alerts": recent, "source": "memory", "count": len(recent)}

    try:
        zcql = (
            "SELECT ROWID, AlertType, Severity, Description, CrimeNo, "
            "DistrictID, Timestamp, Acknowledged FROM Alerts "
            "ORDER BY Timestamp DESC LIMIT 50"
        )
        result = datastore.execute_query(zcql)
        alerts = result.get("data", [])
        return {"alerts": alerts, "source": "datastore", "count": len(alerts)}
    except Exception as e:
        logger.error(f"Alerts query failed: {e}")
        raise HTTPException(status_code=500, detail=f"DataStore query failed: {e}")


@router.delete("/{alert_id}")
async def acknowledge_alert(alert_id: str):
    """Mark an alert as acknowledged (soft delete)."""
    datastore = _get_datastore()

    if datastore is None:
        from alerts.alert_engine import _alert_store
        for alert in _alert_store:
            if str(alert.get("AlertID")) == alert_id:
                alert["Acknowledged"] = True
                return {"success": True, "alert_id": alert_id, "message": "Alert acknowledged"}
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

    try:
        datastore.table("Alerts").update_row(
            {"ROWID": alert_id, "Acknowledged": True}
        )
        return {"success": True, "alert_id": alert_id, "message": "Alert acknowledged"}
    except Exception as e:
        logger.error(f"Alert acknowledge failed for {alert_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {e}")
