import logging
from typing import Optional
from collections import defaultdict

from fastapi import APIRouter, Query, HTTPException

logger = logging.getLogger("kaveri.network")

router = APIRouter()

# Mock data for local development
_MOCK_ACCUSED = [
    {"AccusedName": "Ravi Kumar", "CaseMasterID": "CM001", "DistrictID": "BEU", "CrimeNo": "1BEU0001202600001"},
    {"AccusedName": "Ravi Kumar", "CaseMasterID": "CM002", "DistrictID": "BEU", "CrimeNo": "1BEU0002202600002"},
    {"AccusedName": "Ravi Kumar", "CaseMasterID": "CM003", "DistrictID": "BEU", "CrimeNo": "1BEU0003202600003"},
    {"AccusedName": "Suresh Naik", "CaseMasterID": "CM002", "DistrictID": "BEU", "CrimeNo": "1BEU0002202600002"},
    {"AccusedName": "Suresh Naik", "CaseMasterID": "CM004", "DistrictID": "BEU", "CrimeNo": "1BEU0004202600004"},
    {"AccusedName": "Mohammed Imran", "CaseMasterID": "CM005", "DistrictID": "MYS", "CrimeNo": "1MYS0001202600001"},
    {"AccusedName": "Mohammed Imran", "CaseMasterID": "CM006", "DistrictID": "MYS", "CrimeNo": "1MYS0002202600002"},
    {"AccusedName": "Mohammed Imran", "CaseMasterID": "CM007", "DistrictID": "MYS", "CrimeNo": "1MYS0003202600003"},
    {"AccusedName": "Pradeep Shetty", "CaseMasterID": "CM003", "DistrictID": "BEU", "CrimeNo": "1BEU0003202600003"},
    {"AccusedName": "Pradeep Shetty", "CaseMasterID": "CM004", "DistrictID": "BEU", "CrimeNo": "1BEU0004202600004"},
]


def _get_datastore():
    try:
        import zcatalyst_sdk
        app = zcatalyst_sdk.initialize()
        return app.datastore()
    except Exception:
        return None


def _build_network_from_accused(accused_records: list) -> dict:
    """
    Build vis.js network graph from accused records.

    Nodes = accused persons (sized by number of cases).
    Edges = shared FIR / shared CaseMasterID between two accused.
    """
    # Group by accused name
    accused_cases: dict = defaultdict(set)
    accused_districts: dict = defaultdict(set)
    case_accused: dict = defaultdict(set)

    for record in accused_records:
        name = record.get("AccusedName", "Unknown")
        case_id = record.get("CaseMasterID", record.get("CrimeNo", ""))
        district = record.get("DistrictID", "")
        accused_cases[name].add(case_id)
        accused_districts[name].add(district)
        if case_id:
            case_accused[case_id].add(name)

    # Filter: only accused in 2+ cases
    repeat_accused = {
        name: cases
        for name, cases in accused_cases.items()
        if len(cases) >= 2
    }

    # Build nodes
    nodes = []
    node_ids = {}
    for idx, (name, cases) in enumerate(repeat_accused.items()):
        node_id = idx + 1
        node_ids[name] = node_id
        districts = ", ".join(sorted(accused_districts[name]))
        nodes.append({
            "id": node_id,
            "label": name,
            "title": f"{name}\nCases: {len(cases)}\nDistricts: {districts}",
            "value": len(cases),  # controls node size in vis.js
        })

    # Build edges: connect accused who appear in the same case
    edges = []
    edge_set = set()
    for case_id, names in case_accused.items():
        names_in_repeat = [n for n in names if n in repeat_accused]
        for i, name_a in enumerate(names_in_repeat):
            for name_b in names_in_repeat[i + 1:]:
                edge_key = tuple(sorted([name_a, name_b]))
                if edge_key not in edge_set:
                    edge_set.add(edge_key)
                    id_a = node_ids[name_a]
                    id_b = node_ids[name_b]
                    edges.append({
                        "from": id_a,
                        "to": id_b,
                        "title": f"Co-accused in case {case_id}",
                    })

    return {"nodes": nodes, "edges": edges}


@router.get("")
async def get_network(
    district_id: Optional[str] = Query(None, description="Filter by DistrictID"),
):
    """
    Return criminal network graph data for vis.js.
    Accused persons who appear in 2+ FIRs become nodes;
    shared cases create edges between them.
    """
    datastore = _get_datastore()

    if datastore is None:
        # Local dev fallback
        accused_records = _MOCK_ACCUSED
        if district_id:
            accused_records = [
                r for r in accused_records if r.get("DistrictID") == district_id
            ]
        network = _build_network_from_accused(accused_records)
        return {**network, "source": "memory"}

    try:
        district_clause = f"AND a.DistrictID = '{district_id}'" if district_id else ""
        zcql = (
            f"SELECT a.AccusedName, a.CaseMasterID, a.DistrictID, c.CrimeNo "
            f"FROM Accused a JOIN CaseMaster c ON a.CaseMasterID = c.ROWID "
            f"WHERE 1=1 {district_clause}"
        )
        result = datastore.execute_query(zcql)
        accused_records = result.get("data", [])

        if not accused_records:
            return {"nodes": [], "edges": [], "source": "datastore"}

        network = _build_network_from_accused(accused_records)
        return {**network, "source": "datastore"}

    except Exception as e:
        logger.error(f"Network graph query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Network query failed: {e}")
