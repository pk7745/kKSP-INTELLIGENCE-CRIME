"""
Seed script: Victims and Accused linked to FIR records in CaseMaster.
Run after seed_fir_data.py. ~10 minutes.

Schema per official KSP ER diagram:
  Victim:  VictimMasterID(PK), CaseMasterID(FK), VictimName, AgeYear, GenderID, VictimPolice
  Accused: AccusedMasterID(PK), CaseMasterID(FK), AccusedName, AgeYear, GenderID, PersonID
"""
import os
import sys
import time
import random
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_victims_accused")

try:
    import zcatalyst_sdk as catalyst
    app = catalyst.initialize()
    ds = app.datastore()
    MOCK = False
except Exception:
    logger.warning("Catalyst SDK unavailable — running in mock mode")
    ds = None
    MOCK = True

random.seed(123)

MALE_NAMES = [
    "Ravi Kumar", "Suresh Gowda", "Mahesh Naik", "Ajay Singh", "Rajesh Patil",
    "Vikram Reddy", "Santosh Kumar", "Mohan Das", "Pradeep Nair", "Arun Sharma",
    "Girish Hegde", "Naveen Rao", "Deepak Jadhav", "Anand Kulkarni", "Kiran Pai",
]
FEMALE_NAMES = [
    "Priya Sharma", "Kavitha Reddy", "Anitha Gowda", "Suma Nair", "Lakshmi Patil",
    "Meena Kumar", "Geetha Das", "Sunita Rao", "Rekha Singh", "Manjula Hegde",
]

# GenderID: 1=Male, 2=Female, 3=Transgender — per ER diagram "M/F/T" for Accused
GENDER_ID_MAP = {"M": 1, "F": 2, "T": 3}


def rand_name(gender_code: str) -> str:
    if gender_code == "F":
        return random.choice(FEMALE_NAMES)
    return random.choice(MALE_NAMES)


def get_fir_ids():
    if MOCK:
        return [f"MOCK_FIR_{i:05d}" for i in range(50)]
    try:
        table = ds.table("CaseMaster")
        result = table.get_by_page_token({"page_size": 5000})
        return [row["ROWID"] for row in result.get("data", [])]
    except Exception as e:
        logger.error(f"Could not fetch FIR IDs: {e}")
        return []


def seed_victim(fir_rowid, index: int) -> dict:
    """
    Victim row per ER diagram:
      VictimMasterID (auto by DataStore), CaseMasterID, VictimName,
      AgeYear, GenderID (1=M/2=F/3=T), VictimPolice
    """
    gender_code = random.choice(["M", "F"])
    return {
        "CaseMasterID": fir_rowid,
        "VictimName":   rand_name(gender_code),
        "AgeYear":      random.randint(5, 80),
        "GenderID":     GENDER_ID_MAP[gender_code],
        "VictimPolice": "0",          # 1 if victim is a police officer, else 0
    }


def seed_accused(fir_rowid, index: int) -> dict:
    """
    Accused row per ER diagram:
      AccusedMasterID (auto by DataStore), CaseMasterID, AccusedName,
      AgeYear, GenderID (M/F/T), PersonID (A1, A2, A3…)
    """
    gender_code = random.choices(["M", "F", "T"], weights=[84, 15, 1])[0]
    return {
        "CaseMasterID": fir_rowid,
        "AccusedName":  rand_name(gender_code),
        "AgeYear":      random.randint(16, 55),
        "GenderID":     GENDER_ID_MAP.get(gender_code, 1),
        "PersonID":     f"A{index}",   # Per ER diagram — sorting like A1, A2, A3
    }


def main():
    logger.info("=== KAVERI Victim/Accused Seed ===")
    fir_ids = get_fir_ids()
    logger.info(f"Found {len(fir_ids)} FIR records to process")

    victim_table  = ds.table("Victim")  if not MOCK else None
    accused_table = ds.table("Accused") if not MOCK else None

    victims_seeded  = 0
    accused_seeded  = 0

    for fir_id in fir_ids[:1000]:
        # 1–3 victims per FIR
        for i in range(1, random.choices([1, 2, 3], weights=[70, 25, 5])[0] + 1):
            row = seed_victim(fir_id, i)
            if not MOCK:
                try:
                    victim_table.insert_row(row)
                    time.sleep(0.02)
                    victims_seeded += 1
                except Exception as e:
                    logger.warning(f"Victim skip: {e}")
            else:
                victims_seeded += 1

        # 1–4 accused per FIR
        for i in range(1, random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0] + 1):
            row = seed_accused(fir_id, i)
            if not MOCK:
                try:
                    accused_table.insert_row(row)
                    time.sleep(0.02)
                    accused_seeded += 1
                except Exception as e:
                    logger.warning(f"Accused skip: {e}")
            else:
                accused_seeded += 1

    logger.info(
        f"=== Seeding complete: {victims_seeded} victims, {accused_seeded} accused ==="
    )


if __name__ == "__main__":
    main()
