import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger("kaveri.firs")

router = APIRouter()

# In-memory fallback store for local dev
_fir_memory: list = [
    {
        "CrimeNo": "1BEU0001202600001",
        "CrimeSubHeadID": "THEFT",
        "DistrictID": "BEU",
        "UnitID": "BEU0001",
        "CrimeDateTime": "2026-01-15T14:30:00",
        "Latitude": 12.9716,
        "Longitude": 77.5946,
        "BriefFacts": "Theft of two-wheeler from parking lot near Whitefield IT park.",
        "GravityOffenceID": 3,
        "CaseCategory": "R",
        "InvestigatingOfficerID": "EMP001",
    },
    {
        "CrimeNo": "1MYS0001202600001",
        "CrimeSubHeadID": "ROBBERY",
        "DistrictID": "MYS",
        "UnitID": "MYS0001",
        "CrimeDateTime": "2026-01-15T21:00:00",
        "Latitude": 12.2958,
        "Longitude": 76.6394,
        "BriefFacts": "Armed robbery at jewellery shop. Three accused fled on motorcycle.",
        "GravityOffenceID": 2,
        "CaseCategory": "R",
        "InvestigatingOfficerID": "EMP002",
    },
    {
        "CrimeNo": "1KLB0001202600001",
        "CrimeSubHeadID": "MURDER",
        "DistrictID": "KLB",
        "UnitID": "KLB0001",
        "CrimeDateTime": "2026-01-14T03:15:00",
        "Latitude": 17.3297,
        "Longitude": 76.8200,
        "BriefFacts": "Body of male victim found near irrigation canal. Suspected homicide.",
        "GravityOffenceID": 1,
        "CaseCategory": "R",
        "InvestigatingOfficerID": "EMP003",
    },
]


def _get_datastore():
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


def _build_zcql_fir_list(
    district_id: Optional[str],
    crime_sub_head_id: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    limit: int,
) -> str:
    conditions = ["1=1"]
    if district_id:
        conditions.append(f"DistrictID = '{district_id}'")
    if crime_sub_head_id:
        conditions.append(f"CrimeSubHeadID = '{crime_sub_head_id}'")
    if start_date:
        conditions.append(f"CrimeDateTime >= '{start_date}'")
    if end_date:
        conditions.append(f"CrimeDateTime <= '{end_date}T23:59:59'")
    where = " AND ".join(conditions)
    return (
        f"SELECT CrimeNo, CrimeSubHeadID, DistrictID, UnitID, CrimeDateTime, "
        f"Latitude, Longitude, BriefFacts, GravityOffenceID, CaseCategory, "
        f"InvestigatingOfficerID FROM CaseMaster WHERE {where} "
        f"ORDER BY CrimeDateTime DESC LIMIT {limit}"
    )


@router.get("")
async def list_firs(
    district_id: Optional[str] = Query(None, description="Filter by DistrictID"),
    crime_sub_head_id: Optional[str] = Query(None, description="Filter by crime type"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
):
    """List FIRs with optional filters."""
    datastore = _get_datastore()

    if datastore is None:
        # Local dev fallback
        results = _fir_memory
        if district_id:
            results = [f for f in results if f["DistrictID"] == district_id]
        if crime_sub_head_id:
            results = [f for f in results if f["CrimeSubHeadID"] == crime_sub_head_id]
        return {"firs": results[:limit], "total": len(results), "source": "memory"}

    try:
        zcql = _build_zcql_fir_list(
            district_id, crime_sub_head_id, start_date, end_date, limit
        )
        result = datastore.execute_query(zcql)
        firs = result.get("data", [])
        return {"firs": firs, "total": len(firs), "source": "datastore"}
    except Exception as e:
        logger.error(f"FIR list query failed: {e}")
        raise HTTPException(status_code=500, detail=f"DataStore query failed: {e}")


@router.get("/{crime_no}")
async def get_fir(crime_no: str):
    """Get a single FIR with all related data: victims, accused, sections, chargesheet."""
    datastore = _get_datastore()

    safe_no = crime_no.replace("'", "''")

    if datastore is None:
        # Return from memory store
        fir = next((f for f in _fir_memory if f["CrimeNo"] == crime_no), None)
        if not fir:
            raise HTTPException(status_code=404, detail=f"FIR {crime_no} not found")
        return {
            "fir": fir,
            "victims": [],
            "accused": [],
            "sections": [],
            "chargesheet": None,
            "source": "memory",
        }

    try:
        # Fetch main FIR record
        fir_result = datastore.execute_query(
            f"SELECT * FROM CaseMaster WHERE CrimeNo = '{safe_no}'"
        )
        firs = fir_result.get("data", [])
        if not firs:
            raise HTTPException(status_code=404, detail=f"FIR {crime_no} not found")

        fir = firs[0]
        case_master_id = fir.get("ROWID") or fir.get("CaseMasterID")

        # Fetch related data in parallel
        victims = []
        accused = []
        sections = []
        chargesheet = None

        if case_master_id:
            try:
                v_result = datastore.execute_query(
                    f"SELECT * FROM Victim WHERE CaseMasterID = '{case_master_id}'"
                )
                victims = v_result.get("data", [])
            except Exception as e:
                logger.warning(f"Victim query failed: {e}")

            try:
                a_result = datastore.execute_query(
                    f"SELECT * FROM Accused WHERE CaseMasterID = '{case_master_id}'"
                )
                accused = a_result.get("data", [])
            except Exception as e:
                logger.warning(f"Accused query failed: {e}")

            try:
                s_result = datastore.execute_query(
                    f"SELECT asa.SectionID, s.SectionName, a.ActName "
                    f"FROM ActSectionAssociation asa "
                    f"JOIN Section s ON asa.SectionID = s.ROWID "
                    f"JOIN Act a ON s.ActID = a.ROWID "
                    f"WHERE asa.CaseMasterID = '{case_master_id}'"
                )
                sections = s_result.get("data", [])
            except Exception as e:
                logger.warning(f"Sections query failed: {e}")

            try:
                cs_result = datastore.execute_query(
                    f"SELECT * FROM ChargesheetDetails WHERE CaseMasterID = '{case_master_id}'"
                )
                cs_data = cs_result.get("data", [])
                chargesheet = cs_data[0] if cs_data else None
            except Exception as e:
                logger.warning(f"Chargesheet query failed: {e}")

        return {
            "fir": fir,
            "victims": victims,
            "accused": accused,
            "sections": sections,
            "chargesheet": chargesheet,
            "source": "datastore",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FIR detail query failed for {crime_no}: {e}")
        raise HTTPException(status_code=500, detail=f"DataStore query failed: {e}")
