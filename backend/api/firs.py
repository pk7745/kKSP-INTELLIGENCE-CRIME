"""
FIR list and detail endpoints.
All field names match the official KSP ER diagram (CaseMaster table).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger("kaveri.firs")

router = APIRouter()

# In-memory fallback using official ER diagram field names
_fir_memory: list = [
    {
        "CrimeNo":          "104430001202600001",
        "CaseNo":           "202600001",
        "DistrictID":       "BEU",
        "UnitID":           "0001",
        "PoliceStationID":  1,
        "CaseCategoryID":   1,           # FK→CaseCategory (1=FIR)
        "GravityOffenceID": 3,           # FK→GravityOffence (3=Other Cognizable)
        "CrimeMajorHeadID": 2,           # FK→CrimeHead (2=Crimes Against Property)
        "CrimeMinorHeadID": 5,           # FK→CrimeSubHead (5=Theft)
        "CaseStatusID":     1,           # FK→CaseStatusMaster (1=Under Investigation)
        "IncidentFromDate": "2026-01-15T14:30:00",
        "latitude":         12.9716,
        "longitude":        77.5946,
        "BriefFacts":       "Theft of two-wheeler from parking lot near Whitefield IT park.",
        "InvestigatingOfficerID": "EMP001",
    },
    {
        "CrimeNo":          "104430001202600002",
        "CaseNo":           "202600002",
        "DistrictID":       "MYS",
        "UnitID":           "0001",
        "PoliceStationID":  2,
        "CaseCategoryID":   1,
        "GravityOffenceID": 2,           # 2=Serious Offence
        "CrimeMajorHeadID": 2,           # 2=Crimes Against Property
        "CrimeMinorHeadID": 6,           # 6=Robbery
        "CaseStatusID":     2,           # 2=Charge Sheeted
        "IncidentFromDate": "2026-01-15T21:00:00",
        "latitude":         12.2958,
        "longitude":        76.6394,
        "BriefFacts":       "Armed robbery at jewellery shop. Three accused fled on motorcycle.",
        "InvestigatingOfficerID": "EMP002",
    },
    {
        "CrimeNo":          "104430001202600003",
        "CaseNo":           "202600003",
        "DistrictID":       "KLB",
        "UnitID":           "0001",
        "PoliceStationID":  3,
        "CaseCategoryID":   1,
        "GravityOffenceID": 1,           # 1=Heinous Offence
        "CrimeMajorHeadID": 1,           # 1=Crimes Against Body
        "CrimeMinorHeadID": 1,           # 1=Murder
        "CaseStatusID":     1,
        "IncidentFromDate": "2026-01-14T03:15:00",
        "latitude":         17.3297,
        "longitude":        76.8200,
        "BriefFacts":       "Body of male victim found near irrigation canal. Suspected homicide.",
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
    crime_minor_head_id: Optional[int],
    start_date: Optional[str],
    end_date: Optional[str],
    limit: int,
) -> str:
    conditions = ["1=1"]
    if district_id:
        conditions.append(f"DistrictID = '{district_id}'")
    if crime_minor_head_id:
        conditions.append(f"CrimeMinorHeadID = {crime_minor_head_id}")
    if start_date:
        conditions.append(f"IncidentFromDate >= '{start_date}'")
    if end_date:
        conditions.append(f"IncidentFromDate <= '{end_date}T23:59:59'")
    where = " AND ".join(conditions)
    return (
        f"SELECT CrimeNo, CaseNo, DistrictID, UnitID, PoliceStationID, "
        f"CaseCategoryID, GravityOffenceID, CrimeMajorHeadID, CrimeMinorHeadID, "
        f"CaseStatusID, IncidentFromDate, latitude, longitude, BriefFacts, "
        f"InvestigatingOfficerID FROM CaseMaster WHERE {where} "
        f"ORDER BY IncidentFromDate DESC LIMIT {limit}"
    )


@router.get("")
async def list_firs(
    district_id: Optional[str] = Query(None,  description="Filter by DistrictID"),
    crime_minor_head_id: Optional[int] = Query(None, description="Filter by CrimeMinorHeadID (FK→CrimeSubHead)"),
    start_date: Optional[str] = Query(None,  description="Start date YYYY-MM-DD"),
    end_date:   Optional[str] = Query(None,  description="End date YYYY-MM-DD"),
    limit:      int            = Query(100,   ge=1, le=500),
):
    """List FIRs with optional filters. Field names per official KSP ER diagram."""
    datastore = _get_datastore()

    if datastore is None:
        results = list(_fir_memory)
        if district_id:
            results = [f for f in results if f["DistrictID"] == district_id]
        if crime_minor_head_id:
            results = [f for f in results if f.get("CrimeMinorHeadID") == crime_minor_head_id]
        return {"firs": results[:limit], "total": len(results), "source": "memory"}

    try:
        zcql   = _build_zcql_fir_list(district_id, crime_minor_head_id, start_date, end_date, limit)
        result = datastore.execute_query(zcql)
        firs   = result.get("data", [])
        return {"firs": firs, "total": len(firs), "source": "datastore"}
    except Exception as e:
        logger.error(f"FIR list query failed: {e}")
        raise HTTPException(status_code=500, detail=f"DataStore query failed: {e}")


@router.get("/{crime_no}")
async def get_fir(crime_no: str):
    """Get a single FIR with all related data: victims, accused, sections, chargesheet."""
    datastore = _get_datastore()
    safe_no   = crime_no.replace("'", "''")

    if datastore is None:
        fir = next((f for f in _fir_memory if f["CrimeNo"] == crime_no), None)
        if not fir:
            raise HTTPException(status_code=404, detail=f"FIR {crime_no} not found")
        return {
            "fir": fir, "victims": [], "accused": [],
            "sections": [], "chargesheet": None, "source": "memory",
        }

    try:
        fir_result = datastore.execute_query(
            f"SELECT * FROM CaseMaster WHERE CrimeNo = '{safe_no}'"
        )
        firs = fir_result.get("data", [])
        if not firs:
            raise HTTPException(status_code=404, detail=f"FIR {crime_no} not found")

        fir            = firs[0]
        case_master_id = fir.get("ROWID") or fir.get("CaseMasterID")

        victims = accused = sections = []
        chargesheet = None

        if case_master_id:
            try:
                v = datastore.execute_query(
                    f"SELECT VictimMasterID, VictimName, AgeYear, GenderID, VictimPolice "
                    f"FROM Victim WHERE CaseMasterID = '{case_master_id}'"
                )
                victims = v.get("data", [])
            except Exception as e:
                logger.warning(f"Victim query failed: {e}")

            try:
                a = datastore.execute_query(
                    f"SELECT AccusedMasterID, AccusedName, AgeYear, GenderID, PersonID "
                    f"FROM Accused WHERE CaseMasterID = '{case_master_id}'"
                )
                accused = a.get("data", [])
            except Exception as e:
                logger.warning(f"Accused query failed: {e}")

            try:
                s = datastore.execute_query(
                    f"SELECT asa.SectionID, s.SectionCode, s.SectionDescription, a.ActCode "
                    f"FROM ActSectionAssociation asa "
                    f"JOIN Section s ON asa.SectionID = s.ROWID "
                    f"JOIN Act a ON asa.ActID = a.ROWID "
                    f"WHERE asa.CaseMasterID = '{case_master_id}'"
                )
                sections = s.get("data", [])
            except Exception as e:
                logger.warning(f"Sections query failed: {e}")

            try:
                cs = datastore.execute_query(
                    f"SELECT CSID, csdate, cstype, PolicePersonID "
                    f"FROM ChargesheetDetails WHERE CaseMasterID = '{case_master_id}'"
                )
                cs_data    = cs.get("data", [])
                chargesheet = cs_data[0] if cs_data else None
            except Exception as e:
                logger.warning(f"Chargesheet query failed: {e}")

        return {
            "fir": fir, "victims": victims, "accused": accused,
            "sections": sections, "chargesheet": chargesheet, "source": "datastore",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"FIR detail query failed for {crime_no}: {e}")
        raise HTTPException(status_code=500, detail=f"DataStore query failed: {e}")
