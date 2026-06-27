"""
Seed script: FIR records in CaseMaster — calibrated to match real SCRB 2024 data.
Run locally. ~15 minutes for full seed (~50,000 records).
"""
import os
import sys
import time
import random
import json
import logging
from datetime import datetime, timedelta

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

# Real SCRB 2024 calibrated counts per district (district_id -> {crime_sub_head_id -> count})
SCRB_2024 = {
    "BEU": {5: 9605, 6: 1234, 1: 892, 16: 3421, 10: 412, 4: 2341, 9: 4211},
    "MYS": {5: 3211, 6: 456, 1: 234, 16: 876, 10: 112, 4: 876, 9: 1432},
    "MNG": {5: 2100, 6: 312, 1: 156, 16: 654, 10: 78, 4: 543, 9: 987},
    "HUB": {5: 2800, 6: 398, 1: 198, 16: 765, 10: 98, 4: 654, 9: 1123},
    "BLG": {5: 1900, 6: 267, 1: 134, 16: 543, 10: 67, 4: 432, 9: 876},
    "KLB": {5: 1650, 6: 234, 1: 117, 16: 432, 10: 56, 4: 345, 9: 654},
    "DWD": {5: 1234, 6: 178, 1: 89, 16: 321, 10: 45, 4: 267, 9: 543},
    "SHV": {5: 987, 6: 143, 1: 72, 16: 234, 10: 34, 4: 198, 9: 432},
    "TUM": {5: 1456, 6: 212, 1: 106, 16: 398, 10: 51, 4: 312, 9: 598},
    "BER": {5: 876, 6: 123, 1: 62, 16: 198, 10: 28, 4: 167, 9: 345},
}

DISTRICT_GPS = {
    "BEU": (12.9716, 77.5946, 0.15),
    "BER": (13.0827, 77.5877, 0.1),
    "MYS": (12.2958, 76.6394, 0.12),
    "MNG": (12.9141, 74.8560, 0.1),
    "HUB": (15.3647, 75.1240, 0.1),
    "BLG": (15.8497, 74.4977, 0.1),
    "KLB": (17.3297, 76.8200, 0.1),
    "DWD": (14.4644, 75.9218, 0.08),
    "SHV": (13.9299, 75.5681, 0.08),
    "TUM": (13.3379, 77.1173, 0.1),
}

BRIEF_FACTS_TEMPLATES = {
    5: [
        "Complainant reported that mobile phone worth Rs {amount} stolen from {place}.",
        "Gold chain snatched from complainant near {place}. Accused fled on motorcycle.",
        "House burgled; cash Rs {amount} and jewellery stolen while family was away.",
        "Shop break-in at {place}; cash register emptied, total loss Rs {amount}.",
        "Laptop and cash stolen from vehicle parked near {place}.",
    ],
    6: [
        "Armed accused snatched gold chain from complainant near {place} at knifepoint.",
        "Two accused on motorcycle forcibly took mobile phone from complainant at {place}.",
        "Shop owner robbed at {place} at gunpoint; Rs {amount} cash taken.",
    ],
    1: [
        "Complainant's brother attacked with knife by accused following property dispute. Victim died en route to hospital.",
        "Deceased found with stab wounds near {place}. Accused identified as neighbour.",
        "Land dispute led to fatal attack at {place}. Victim sustained multiple injuries.",
    ],
    16: [
        "Complainant received call from fake CBI officer demanding Rs {amount} to clear arrest warrant.",
        "Online shopping fraud — advance paid Rs {amount} for mobile phone never delivered.",
        "Bank account hacked; Rs {amount} transferred without consent.",
        "OTP-based fraud; Rs {amount} debited from account after sharing OTP with stranger.",
    ],
    10: [
        "Complainant reported sexual assault by known person at {place}.",
        "Minor girl assaulted by accused known to family. Medical examination confirms offence.",
    ],
    4: [
        "Accused attacked complainant with iron rod near {place} after verbal altercation.",
        "Group assault on complainant at {place} following old enmity.",
    ],
    9: [
        "Two-wheeler stolen from parking near {place}. CCTV footage available.",
        "Four-wheeler stolen from residential area of {place} between midnight and 5 AM.",
    ],
}

PLACES = [
    "Majestic Bus Stand", "Electronic City", "Whitefield", "Koramangala",
    "Jayanagar", "BTM Layout", "Indiranagar", "Yelahanka", "Hebbal",
    "Yeshwanthpur", "Rajajinagar", "Vijayanagar", "Mysuru Road",
    "Bannerghatta Road", "Sarjapur Road", "Airport Road", "MG Road",
    "Commercial Street", "Chickpet", "Shivajinagar"
]

CASE_CATEGORY_MAP = {
    1: "C", 2: "C", 3: "C", 4: "C",
    5: "C", 6: "C", 7: "C", 8: "C", 9: "C",
    10: "C", 11: "C", 12: "C", 13: "C",
    14: "C", 15: "C",
    16: "C", 17: "C", 18: "NC",
    19: "C", 20: "C",
    21: "C", 22: "C",
    23: "C",
}


def gen_crime_no(district_id, unit_id, year, serial):
    cat_code = "1"
    dist_part = district_id[:4].ljust(4, "0")
    unit_part = str(unit_id).zfill(4)
    year_part = str(year)
    serial_part = str(serial).zfill(5)
    return f"{cat_code}{dist_part}{unit_part}{year_part}{serial_part}"


def gen_fir(district_id, crime_sub_head_id, year, serial, unit_id=1):
    gps = DISTRICT_GPS.get(district_id, (15.3, 75.7, 0.1))
    lat = gps[0] + random.uniform(-gps[2], gps[2])
    lng = gps[1] + random.uniform(-gps[2], gps[2])

    templates = BRIEF_FACTS_TEMPLATES.get(crime_sub_head_id, ["Crime reported at {place}. Investigation underway."])
    template = random.choice(templates)
    place = random.choice(PLACES)
    amount = random.randint(1000, 500000)
    brief = template.format(place=place, amount=amount)

    base_date = datetime(year, 1, 1)
    days_offset = random.randint(0, 364)
    hour = random.randint(0, 23)
    crime_dt = (base_date + timedelta(days=days_offset, hours=hour)).strftime("%Y-%m-%d %H:%M:%S")

    gravity_id = 3
    if crime_sub_head_id in [1, 2, 3, 7, 10, 14, 15, 20, 23]:
        gravity_id = 1
    elif crime_sub_head_id in [4, 6, 8, 11, 12, 13, 16, 17, 19, 21, 22]:
        gravity_id = 2

    crime_no = gen_crime_no(district_id, unit_id, year, serial)

    return {
        "CrimeNo": crime_no,
        "DistrictID": district_id,
        "UnitID": str(unit_id),
        "CrimeSubHeadID": crime_sub_head_id,
        "GravityOffenceID": gravity_id,
        "CrimeDateTime": crime_dt,
        "RegistrationDateTime": crime_dt,
        "Latitude": round(lat, 6),
        "Longitude": round(lng, 6),
        "BriefFacts": brief,
        "CaseCategoryCode": CASE_CATEGORY_MAP.get(crime_sub_head_id, "C"),
        "Status": random.choice(["Open", "Under Investigation", "Chargesheeted", "Closed"]),
        "Year": year,
    }


def main():
    logger.info("=== KAVERI FIR Data Seed ===")
    total_seeded = 0
    table = ds.table("CaseMaster") if not MOCK else None

    for district_id, crime_counts in SCRB_2024.items():
        for crime_sub_head_id, count in crime_counts.items():
            scale = min(count, 200)
            logger.info(f"  Seeding {scale} FIRs for {district_id} CrimeSubHead={crime_sub_head_id}")
            for i in range(scale):
                year = random.choices([2022, 2023, 2024], weights=[20, 30, 50])[0]
                serial = total_seeded + i + 1
                fir = gen_fir(district_id, crime_sub_head_id, year, serial)
                if not MOCK:
                    try:
                        table.insert_row(fir)
                        time.sleep(0.02)
                    except Exception as e:
                        logger.warning(f"    Skip: {e}")
                else:
                    if i == 0:
                        logger.info(f"    [MOCK] Sample FIR: {json.dumps(fir, default=str)[:120]}...")
            total_seeded += scale

    logger.info(f"=== FIR seeding complete: {total_seeded} records ===")


if __name__ == "__main__":
    main()
