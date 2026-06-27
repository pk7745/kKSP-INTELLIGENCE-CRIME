"""
Seed script: DistrictDemographics and SeasonalPatterns.
Run locally before deploying. ~1 minute.
"""
import os
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demographics")

try:
    import zcatalyst_sdk as catalyst
    app = catalyst.initialize()
    ds = app.datastore()
    MOCK = False
except Exception:
    logger.warning("Catalyst SDK unavailable — running in mock mode")
    ds = None
    MOCK = True

DISTRICT_DEMOGRAPHICS = [
    {"DistrictID": "BEU", "DistrictName": "Bengaluru Urban", "Population": 12000000, "PopulationDensity": 4381, "LiteracyRate": 88.5, "YouthPercent": 32.1, "PovertyRate": 9.8, "MigrantPercent": 35.2, "UrbanPercent": 98.0, "UnemploymentRate": 5.2},
    {"DistrictID": "BER", "DistrictName": "Bengaluru Rural", "Population": 990000, "PopulationDensity": 298, "LiteracyRate": 77.2, "YouthPercent": 28.4, "PovertyRate": 18.6, "MigrantPercent": 12.1, "UrbanPercent": 22.4, "UnemploymentRate": 8.1},
    {"DistrictID": "MYS", "DistrictName": "Mysuru", "Population": 3000000, "PopulationDensity": 443, "LiteracyRate": 76.5, "YouthPercent": 27.8, "PovertyRate": 17.3, "MigrantPercent": 8.4, "UrbanPercent": 38.2, "UnemploymentRate": 7.3},
    {"DistrictID": "MNG", "DistrictName": "Mangaluru", "Population": 2090000, "PopulationDensity": 327, "LiteracyRate": 86.3, "YouthPercent": 25.1, "PovertyRate": 12.1, "MigrantPercent": 14.2, "UrbanPercent": 45.6, "UnemploymentRate": 6.1},
    {"DistrictID": "HUB", "DistrictName": "Hubballi-Dharwad", "Population": 2430000, "PopulationDensity": 368, "LiteracyRate": 78.9, "YouthPercent": 29.3, "PovertyRate": 15.7, "MigrantPercent": 11.3, "UrbanPercent": 52.3, "UnemploymentRate": 7.8},
    {"DistrictID": "BLG", "DistrictName": "Belagavi", "Population": 4780000, "PopulationDensity": 324, "LiteracyRate": 72.1, "YouthPercent": 30.2, "PovertyRate": 22.4, "MigrantPercent": 7.8, "UrbanPercent": 27.4, "UnemploymentRate": 9.2},
    {"DistrictID": "KLB", "DistrictName": "Kalaburagi", "Population": 2760000, "PopulationDensity": 218, "LiteracyRate": 64.8, "YouthPercent": 31.5, "PovertyRate": 28.3, "MigrantPercent": 6.2, "UrbanPercent": 33.1, "UnemploymentRate": 11.4},
    {"DistrictID": "DWD", "DistrictName": "Davanagere", "Population": 1980000, "PopulationDensity": 259, "LiteracyRate": 73.4, "YouthPercent": 28.9, "PovertyRate": 20.1, "MigrantPercent": 8.9, "UrbanPercent": 36.8, "UnemploymentRate": 9.6},
    {"DistrictID": "SHV", "DistrictName": "Shivamogga", "Population": 1760000, "PopulationDensity": 183, "LiteracyRate": 79.8, "YouthPercent": 26.7, "PovertyRate": 16.2, "MigrantPercent": 7.4, "UrbanPercent": 34.2, "UnemploymentRate": 7.9},
    {"DistrictID": "TUM", "DistrictName": "Tumakuru", "Population": 2680000, "PopulationDensity": 227, "LiteracyRate": 75.3, "YouthPercent": 27.6, "PovertyRate": 19.8, "MigrantPercent": 9.1, "UrbanPercent": 28.7, "UnemploymentRate": 8.7},
]

SEASONAL_PATTERNS = [
    {"Month": 1, "MonthName": "January", "Festival": "Sankranti", "CrimeMultiplier": 1.05, "PeakCrimeType": "Theft", "Notes": "Harvest season; increased outdoor gatherings"},
    {"Month": 2, "MonthName": "February", "Festival": "None", "CrimeMultiplier": 0.95, "PeakCrimeType": "Cyber Crime", "Notes": "Relatively quiet month"},
    {"Month": 3, "MonthName": "March", "Festival": "Holi / Ugadi", "CrimeMultiplier": 1.10, "PeakCrimeType": "Assault", "Notes": "Holi and Ugadi; alcohol-related incidents increase"},
    {"Month": 4, "MonthName": "April", "Festival": "Ugadi / Ram Navami", "CrimeMultiplier": 1.08, "PeakCrimeType": "Communal", "Notes": "Religious processions; heightened security required"},
    {"Month": 5, "MonthName": "May", "Festival": "None", "CrimeMultiplier": 0.92, "PeakCrimeType": "Theft", "Notes": "Summer; lower outdoor activity"},
    {"Month": 6, "MonthName": "June", "Festival": "Eid", "CrimeMultiplier": 1.03, "PeakCrimeType": "Theft", "Notes": "Monsoon onset; chain snatching increases"},
    {"Month": 7, "MonthName": "July", "Festival": "None", "CrimeMultiplier": 0.98, "PeakCrimeType": "Robbery", "Notes": "Monsoon; lower visibility aids crime"},
    {"Month": 8, "MonthName": "August", "Festival": "Independence Day / Raksha Bandhan", "CrimeMultiplier": 1.02, "PeakCrimeType": "Theft", "Notes": "Public gatherings; pickpocketing increases"},
    {"Month": 9, "MonthName": "September", "Festival": "Ganesh Chaturthi", "CrimeMultiplier": 1.12, "PeakCrimeType": "Theft", "Notes": "Major festival; large crowds; theft spike"},
    {"Month": 10, "MonthName": "October", "Festival": "Navaratri / Dasara", "CrimeMultiplier": 1.35, "PeakCrimeType": "Theft", "Notes": "Mysuru Dasara — highest crime multiplier of year; jewellery theft, pickpocketing, chain snatching"},
    {"Month": 11, "MonthName": "November", "Festival": "Deepavali", "CrimeMultiplier": 1.28, "PeakCrimeType": "Theft", "Notes": "Deepavali; gold purchases → chain snatching spike; cracker-related incidents"},
    {"Month": 12, "MonthName": "December", "Festival": "Christmas / New Year", "CrimeMultiplier": 1.15, "PeakCrimeType": "Drunk Driving", "Notes": "Year-end celebrations; drunk driving, assault in entertainment districts"},
]


def seed_table(name, rows):
    if MOCK:
        logger.info(f"[MOCK] Would insert {len(rows)} rows into {name}")
        return
    table = ds.table(name)
    count = 0
    for row in rows:
        try:
            table.insert_row(row)
            count += 1
            time.sleep(0.05)
        except Exception as e:
            logger.warning(f"  Skip {name}: {e}")
    logger.info(f"  Seeded {count}/{len(rows)} into {name}")


def main():
    logger.info("=== KAVERI Demographics + Seasonal Seed ===")
    seed_table("DistrictDemographics", DISTRICT_DEMOGRAPHICS)
    seed_table("SeasonalPatterns", SEASONAL_PATTERNS)
    logger.info("=== Complete ===")


if __name__ == "__main__":
    main()
