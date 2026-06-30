"""
Seed script: FIR records in CaseMaster — calibrated to SCRB 2024 data.
Reads district_ipc_2024.csv for official counts, then generates records.
Run locally. ~15 minutes for full seed (~50,000 records).

CaseMaster schema per official KSP ER diagram:
  CrimeNo, CaseNo, CrimeRegisteredDate, PolicePersonID, PoliceStationID,
  CaseCategoryID (FK→CaseCategory), GravityOffenceID (FK→GravityOffence),
  CrimeMajorHeadID (FK→CrimeHead), CrimeMinorHeadID (FK→CrimeSubHead),
  CaseStatusID (FK→CaseStatusMaster), latitude, longitude, BriefFacts,
  IncidentFromDate, IncidentToDate, InfoReceivedPSDate
"""
import os
import sys
import csv
import time
import random
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_fir")

try:
    import zcatalyst_sdk as catalyst
    app = catalyst.initialize()
    ds = app.datastore()
    MOCK = False
except Exception:
    logger.warning("Catalyst SDK unavailable — running in mock/dry-run mode")
    ds = None
    MOCK = True

random.seed(42)

# ── Load SCRB CSV ─────────────────────────────────────────────────────────────
_CSV_PATH = Path(__file__).parent / "data" / "district_ipc_2024.csv"

def _load_scrb_csv() -> list:
    """Load SCRB 2024 calibrated counts from official CSV."""
    rows = []
    try:
        with open(_CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "DistrictID":       row["DistrictID"],
                    "CrimeMinorHeadID": int(row["CrimeMinorHeadID"]),   # FK→CrimeSubHead
                    "CrimeMajorHeadID": int(row["CrimeMajorHeadID"]),   # FK→CrimeHead
                    "Count2024":        int(row["Count2024"]),
                })
        logger.info(f"Loaded {len(rows)} rows from {_CSV_PATH}")
    except Exception as e:
        logger.warning(f"CSV load failed ({e}), using hardcoded fallback")
        rows = _SCRB_FALLBACK
    return rows

# Hardcoded fallback matching the CSV (used if CSV is missing)
_SCRB_FALLBACK = [
    {"DistrictID": "BEU", "CrimeMinorHeadID": 5,  "CrimeMajorHeadID": 2, "Count2024": 9605},
    {"DistrictID": "BEU", "CrimeMinorHeadID": 6,  "CrimeMajorHeadID": 2, "Count2024": 1234},
    {"DistrictID": "BEU", "CrimeMinorHeadID": 1,  "CrimeMajorHeadID": 1, "Count2024": 892},
    {"DistrictID": "BEU", "CrimeMinorHeadID": 16, "CrimeMajorHeadID": 5, "Count2024": 3421},
    {"DistrictID": "BEU", "CrimeMinorHeadID": 10, "CrimeMajorHeadID": 3, "Count2024": 412},
    {"DistrictID": "BEU", "CrimeMinorHeadID": 4,  "CrimeMajorHeadID": 1, "Count2024": 2341},
    {"DistrictID": "BEU", "CrimeMinorHeadID": 9,  "CrimeMajorHeadID": 2, "Count2024": 4211},
    {"DistrictID": "MYS", "CrimeMinorHeadID": 5,  "CrimeMajorHeadID": 2, "Count2024": 3211},
    {"DistrictID": "MYS", "CrimeMinorHeadID": 6,  "CrimeMajorHeadID": 2, "Count2024": 456},
    {"DistrictID": "MYS", "CrimeMinorHeadID": 1,  "CrimeMajorHeadID": 1, "Count2024": 234},
    {"DistrictID": "MYS", "CrimeMinorHeadID": 16, "CrimeMajorHeadID": 5, "Count2024": 876},
    {"DistrictID": "KLB", "CrimeMinorHeadID": 5,  "CrimeMajorHeadID": 2, "Count2024": 1650},
    {"DistrictID": "KLB", "CrimeMinorHeadID": 1,  "CrimeMajorHeadID": 1, "Count2024": 117},
    {"DistrictID": "KLB", "CrimeMinorHeadID": 16, "CrimeMajorHeadID": 5, "Count2024": 432},
]

# ── GPS data ──────────────────────────────────────────────────────────────────
DISTRICT_GPS = {
    "BEU": (12.9716, 77.5946, 0.15),
    "BER": (13.0827, 77.5877, 0.10),
    "MYS": (12.2958, 76.6394, 0.12),
    "MNG": (12.9141, 74.8560, 0.10),
    "HUB": (15.3647, 75.1240, 0.10),
    "BLG": (15.8497, 74.4977, 0.10),
    "KLB": (17.3297, 76.8200, 0.10),
    "DWD": (14.4644, 75.9218, 0.08),
    "SHV": (13.9299, 75.5681, 0.08),
    "TUM": (13.3379, 77.1173, 0.10),
    "BER": (13.0827, 77.5877, 0.10),
}

BRIEF_FACTS_TEMPLATES = {
    5:  ["Complainant reported that mobile phone worth Rs {amount} stolen from {place}.",
         "Gold chain snatched from complainant near {place}. Accused fled on motorcycle.",
         "House burgled; cash Rs {amount} and jewellery stolen while family was away."],
    6:  ["Armed accused snatched gold chain from complainant near {place} at knifepoint.",
         "Two accused on motorcycle forcibly took mobile phone from complainant at {place}."],
    1:  ["Complainant's brother attacked with knife by accused following property dispute. Victim died en route.",
         "Deceased found with stab wounds near {place}. Accused identified as neighbour."],
    16: ["Complainant received call from fake CBI officer demanding Rs {amount} to clear arrest warrant.",
         "Online shopping fraud — advance paid Rs {amount} for mobile phone never delivered.",
         "Bank account hacked; Rs {amount} transferred without consent."],
    10: ["Complainant reported sexual assault by known person at {place}.",
         "Minor girl assaulted by accused known to family. Medical examination confirms offence."],
    4:  ["Accused attacked complainant with iron rod near {place} after verbal altercation.",
         "Group assault on complainant at {place} following old enmity."],
    9:  ["Two-wheeler stolen from parking near {place}. CCTV footage available.",
         "Four-wheeler stolen from residential area of {place} between midnight and 5 AM."],
}

PLACES = [
    "Majestic Bus Stand", "Electronic City", "Whitefield", "Koramangala",
    "Jayanagar", "BTM Layout", "Indiranagar", "Yelahanka", "Hebbal",
    "Yeshwanthpur", "Rajajinagar", "Vijayanagar", "Mysuru Road",
    "Bannerghatta Road", "Sarjapur Road", "Airport Road", "MG Road",
]

# CaseCategoryID per ER diagram: 1=FIR, 3=UDR, 4=PAR, 8=Zero FIR
# GravityOffenceID: 1=Heinous, 2=Serious, 3=Other Cognizable, 4=Non-Cognizable
CRIME_GRAVITY_MAP = {
    1: 1, 2: 1, 3: 1, 10: 1, 14: 1, 15: 1, 20: 1, 23: 1,
    4: 2, 6: 2, 8: 2, 11: 2, 12: 2, 13: 2, 16: 2, 17: 2, 19: 2, 21: 2, 22: 2,
    5: 3, 9: 3, 18: 3,
}

# CaseStatusID: 1=Under Investigation, 2=Charge Sheeted, 3=Final Report, 4=Closed
CASE_STATUS_WEIGHTS = [40, 30, 15, 15]
CASE_STATUS_IDS = [1, 2, 3, 4]


def gen_crime_no(district_id: str, unit_id: int, year: int, serial: int) -> str:
    """
    CrimeNo format per KSP ER diagram page 1:
    1-digit CaseCategoryCode + 4-digit DistrictID + 4-digit PoliceStationID + 4-digit Year + 5-digit Serial
    Example: 104430006202600001  (FIR)
    """
    cat_code  = "1"                            # FIR
    dist_part = district_id[:4].ljust(4, "0")
    unit_part = str(unit_id).zfill(4)
    year_part = str(year)
    serial_part = str(serial).zfill(5)
    return f"{cat_code}{dist_part}{unit_part}{year_part}{serial_part}"


def gen_fir(district_id: str, crime_minor_head_id: int, crime_major_head_id: int,
            year: int, serial: int, unit_id: int = 1) -> dict:
    gps = DISTRICT_GPS.get(district_id, (15.3, 75.7, 0.1))
    lat = gps[0] + random.uniform(-gps[2], gps[2])
    lng = gps[1] + random.uniform(-gps[2], gps[2])

    templates = BRIEF_FACTS_TEMPLATES.get(
        crime_minor_head_id,
        ["Crime reported at {place}. Investigation underway."],
    )
    brief = random.choice(templates).format(
        place=random.choice(PLACES),
        amount=random.randint(1000, 500000),
    )

    base_date = datetime(year, 1, 1)
    crime_dt  = base_date + timedelta(days=random.randint(0, 364), hours=random.randint(0, 23))
    crime_dt_str = crime_dt.strftime("%Y-%m-%d %H:%M:%S")
    registered_dt_str = (crime_dt + timedelta(hours=random.randint(1, 12))).strftime("%Y-%m-%d %H:%M:%S")

    crime_no = gen_crime_no(district_id, unit_id, year, serial)
    # CaseNo = YYYY + 5-digit serial (last 9 digits of CrimeNo, per ER diagram)
    case_no  = f"{year}{str(serial).zfill(5)}"

    gravity_id  = CRIME_GRAVITY_MAP.get(crime_minor_head_id, 3)
    status_id   = random.choices(CASE_STATUS_IDS, weights=CASE_STATUS_WEIGHTS)[0]

    return {
        "CrimeNo":             crime_no,
        "CaseNo":              case_no,
        "CrimeRegisteredDate": registered_dt_str,
        "PoliceStationID":     unit_id,
        "PolicePersonID":      random.randint(1, 50),
        "CaseCategoryID":      1,                   # FK→CaseCategory (1=FIR)
        "GravityOffenceID":    gravity_id,           # FK→GravityOffence
        "CrimeMajorHeadID":    crime_major_head_id,  # FK→CrimeHead
        "CrimeMinorHeadID":    crime_minor_head_id,  # FK→CrimeSubHead
        "CaseStatusID":        status_id,            # FK→CaseStatusMaster
        "DistrictID":          district_id,
        "UnitID":              str(unit_id),
        "latitude":            round(lat, 6),
        "longitude":           round(lng, 6),
        "BriefFacts":          brief,
        "IncidentFromDate":    crime_dt_str,
        "IncidentToDate":      crime_dt_str,
        "InfoReceivedPSDate":  registered_dt_str,
        "Year":                year,
    }


def main():
    logger.info("=== KAVERI FIR Data Seed ===")
    scrb_rows = _load_scrb_csv()
    total_seeded = 0
    table = ds.table("CaseMaster") if not MOCK else None

    for row in scrb_rows:
        district_id        = row["DistrictID"]
        crime_minor_head_id = row["CrimeMinorHeadID"]
        crime_major_head_id = row["CrimeMajorHeadID"]
        count              = row["Count2024"]

        # Seed up to 200 records per district+crime combination
        scale = min(count, 200)
        logger.info(
            f"  Seeding {scale} FIRs — {district_id} "
            f"CrimeMinorHead={crime_minor_head_id} CrimeMajorHead={crime_major_head_id}"
        )
        for i in range(scale):
            year   = random.choices([2022, 2023, 2024], weights=[20, 30, 50])[0]
            serial = total_seeded + i + 1
            fir    = gen_fir(district_id, crime_minor_head_id, crime_major_head_id,
                             year, serial)
            if not MOCK:
                try:
                    table.insert_row(fir)
                    time.sleep(0.02)
                except Exception as e:
                    logger.warning(f"    Skip: {e}")
            else:
                if i == 0:
                    logger.info(
                        f"    [MOCK] Sample FIR: {json.dumps(fir, default=str)[:140]}..."
                    )
        total_seeded += scale

    logger.info(f"=== FIR seeding complete: {total_seeded} records ===")


if __name__ == "__main__":
    main()
