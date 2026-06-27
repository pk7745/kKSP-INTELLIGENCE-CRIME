"""
Seed script: Victims and Accused linked to FIR records in CaseMaster.
Run after seed_fir_data.py. ~10 minutes.
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
PLACES = ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru", "Belagavi", "Kalaburagi", "Davanagere"]
OCCUPATIONS = ["Labourer", "Farmer", "Student", "Driver", "Shopkeeper", "Unemployed", "Businessman", "Homemaker"]
RELIGIONS = ["Hindu", "Muslim", "Christian", "Jain", "Buddhist", "Sikh"]


def rand_age(min_a=18, max_a=65):
    return random.randint(min_a, max_a)


def rand_name(gender=None):
    if gender == "F":
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


def seed_victim(fir_rowid, index):
    gender = random.choice(["M", "F"])
    age = rand_age(5, 80)
    name = rand_name(gender)
    return {
        "CaseMasterROWID": fir_rowid,
        "VictimNo": f"V{index}",
        "VictimName": name,
        "Age": age,
        "Gender": gender,
        "Religion": random.choice(RELIGIONS),
        "Occupation": random.choice(OCCUPATIONS),
        "InjuryType": random.choice(["None", "Minor", "Grievous", "Fatal"]),
        "NativePlace": random.choice(PLACES),
    }


def seed_accused(fir_rowid, index):
    gender = random.choices(["M", "F"], weights=[85, 15])[0]
    age = rand_age(16, 55)
    name = rand_name(gender)
    return {
        "CaseMasterROWID": fir_rowid,
        "AccusedNo": f"A{index}",
        "AccusedName": name,
        "Age": age,
        "Gender": gender,
        "Religion": random.choice(RELIGIONS),
        "Occupation": random.choice(OCCUPATIONS),
        "NativePlace": random.choice(PLACES),
        "PriorCases": random.randint(0, 5),
        "ArrestStatus": random.choice(["Arrested", "Absconding", "Surrendered", "Not Identified"]),
    }


def main():
    logger.info("=== KAVERI Victim/Accused Seed ===")
    fir_ids = get_fir_ids()
    logger.info(f"Found {len(fir_ids)} FIR records to process")

    victim_table = ds.table("Victim") if not MOCK else None
    accused_table = ds.table("Accused") if not MOCK else None

    victims_seeded = 0
    accused_seeded = 0

    for fir_id in fir_ids[:1000]:
        num_victims = random.choices([1, 2, 3], weights=[70, 25, 5])[0]
        for i in range(1, num_victims + 1):
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

        num_accused = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
        for i in range(1, num_accused + 1):
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

    logger.info(f"=== Complete: {victims_seeded} victims, {accused_seeded} accused seeded ===")


if __name__ == "__main__":
    main()
