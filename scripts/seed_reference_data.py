"""
Seed script: Reference data — States, Districts, Units, Acts, Sections, Ranks, CrimeHeads, CrimeSubHeads.
Run locally before deploying. Uploads to Catalyst DataStore.
"""
import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_reference")

try:
    import zcatalyst_sdk as catalyst
    app = catalyst.initialize()
    ds = app.datastore()
    MOCK = False
except Exception:
    logger.warning("Catalyst SDK unavailable — running in mock mode (data will be printed only)")
    ds = None
    MOCK = True

STATES = [
    {"StateID": 29, "StateName": "Karnataka", "StateCode": "KA"},
]

DISTRICTS = [
    {"DistrictID": "BEU", "DistrictName": "Bengaluru Urban", "StateID": 29, "Latitude": 12.9716, "Longitude": 77.5946, "Population": 12000000},
    {"DistrictID": "BER", "DistrictName": "Bengaluru Rural", "StateID": 29, "Latitude": 13.0827, "Longitude": 77.5877, "Population": 990000},
    {"DistrictID": "MYS", "DistrictName": "Mysuru", "StateID": 29, "Latitude": 12.2958, "Longitude": 76.6394, "Population": 3000000},
    {"DistrictID": "MNG", "DistrictName": "Mangaluru", "StateID": 29, "Latitude": 12.9141, "Longitude": 74.8560, "Population": 2090000},
    {"DistrictID": "HUB", "DistrictName": "Hubballi-Dharwad", "StateID": 29, "Latitude": 15.3647, "Longitude": 75.1240, "Population": 2430000},
    {"DistrictID": "BLG", "DistrictName": "Belagavi", "StateID": 29, "Latitude": 15.8497, "Longitude": 74.4977, "Population": 4780000},
    {"DistrictID": "KLB", "DistrictName": "Kalaburagi", "StateID": 29, "Latitude": 17.3297, "Longitude": 76.8200, "Population": 2760000},
    {"DistrictID": "DWD", "DistrictName": "Davanagere", "StateID": 29, "Latitude": 14.4644, "Longitude": 75.9218, "Population": 1980000},
    {"DistrictID": "SHV", "DistrictName": "Shivamogga", "StateID": 29, "Latitude": 13.9299, "Longitude": 75.5681, "Population": 1760000},
    {"DistrictID": "TUM", "DistrictName": "Tumakuru", "StateID": 29, "Latitude": 13.3379, "Longitude": 77.1173, "Population": 2680000},
    {"DistrictID": "KOL", "DistrictName": "Kolar", "StateID": 29, "Latitude": 13.1363, "Longitude": 78.1294, "Population": 1540000},
    {"DistrictID": "CHI", "DistrictName": "Chikkaballapur", "StateID": 29, "Latitude": 13.4355, "Longitude": 77.7310, "Population": 1250000},
    {"DistrictID": "RAM", "DistrictName": "Ramanagara", "StateID": 29, "Latitude": 12.7157, "Longitude": 77.2804, "Population": 1080000},
    {"DistrictID": "CKM", "DistrictName": "Chikkamagaluru", "StateID": 29, "Latitude": 13.3161, "Longitude": 75.7720, "Population": 1140000},
    {"DistrictID": "HAS", "DistrictName": "Hassan", "StateID": 29, "Latitude": 13.0035, "Longitude": 76.1004, "Population": 1770000},
    {"DistrictID": "MDY", "DistrictName": "Mandya", "StateID": 29, "Latitude": 12.5218, "Longitude": 76.8951, "Population": 1800000},
    {"DistrictID": "CHN", "DistrictName": "Chamarajanagar", "StateID": 29, "Latitude": 11.9261, "Longitude": 76.9440, "Population": 1010000},
    {"DistrictID": "KOD", "DistrictName": "Kodagu", "StateID": 29, "Latitude": 12.4244, "Longitude": 75.7382, "Population": 556000},
    {"DistrictID": "DKS", "DistrictName": "Dakshina Kannada", "StateID": 29, "Latitude": 12.8438, "Longitude": 75.2479, "Population": 2090000},
    {"DistrictID": "UDU", "DistrictName": "Udupi", "StateID": 29, "Latitude": 13.3409, "Longitude": 74.7421, "Population": 1180000},
    {"DistrictID": "UKN", "DistrictName": "Uttara Kannada", "StateID": 29, "Latitude": 14.7902, "Longitude": 74.6800, "Population": 1440000},
    {"DistrictID": "GDA", "DistrictName": "Gadag", "StateID": 29, "Latitude": 15.4316, "Longitude": 75.6355, "Population": 1070000},
    {"DistrictID": "DHR", "DistrictName": "Dharwad", "StateID": 29, "Latitude": 15.4589, "Longitude": 75.0078, "Population": 1850000},
    {"DistrictID": "BPR", "DistrictName": "Bagalkot", "StateID": 29, "Latitude": 16.1802, "Longitude": 75.6968, "Population": 1890000},
    {"DistrictID": "VJP", "DistrictName": "Vijayapura", "StateID": 29, "Latitude": 16.8302, "Longitude": 75.7100, "Population": 2170000},
    {"DistrictID": "BDR", "DistrictName": "Bidar", "StateID": 29, "Latitude": 17.9104, "Longitude": 77.5199, "Population": 1720000},
    {"DistrictID": "YDG", "DistrictName": "Yadgir", "StateID": 29, "Latitude": 16.7710, "Longitude": 77.1384, "Population": 1180000},
    {"DistrictID": "RCH", "DistrictName": "Raichur", "StateID": 29, "Latitude": 16.2120, "Longitude": 77.3439, "Population": 1930000},
    {"DistrictID": "KPN", "DistrictName": "Koppal", "StateID": 29, "Latitude": 15.3508, "Longitude": 76.1547, "Population": 1390000},
    {"DistrictID": "BGT", "DistrictName": "Ballari", "StateID": 29, "Latitude": 15.1394, "Longitude": 76.9214, "Population": 2540000},
    {"DistrictID": "CHD", "DistrictName": "Chitradurga", "StateID": 29, "Latitude": 14.2251, "Longitude": 76.3981, "Population": 1660000},
    {"DistrictID": "VJN", "DistrictName": "Vijayapura (Bijapur)", "StateID": 29, "Latitude": 16.8302, "Longitude": 75.7100, "Population": 2170000},
    {"DistrictID": "TDV", "DistrictName": "Tumkur Division", "StateID": 29, "Latitude": 13.3379, "Longitude": 77.1173, "Population": 2680000},
    {"DistrictID": "MYD", "DistrictName": "Mysuru Division", "StateID": 29, "Latitude": 12.2958, "Longitude": 76.6394, "Population": 3000000},
    {"DistrictID": "RNG", "DistrictName": "Ramnagara", "StateID": 29, "Latitude": 12.7157, "Longitude": 77.2804, "Population": 1080000},
    {"DistrictID": "CLG", "DistrictName": "Chikkamagalur", "StateID": 29, "Latitude": 13.3161, "Longitude": 75.7720, "Population": 1140000},
    {"DistrictID": "BNP", "DistrictName": "Bidar North Patrol", "StateID": 29, "Latitude": 17.9104, "Longitude": 77.5199, "Population": 860000},
    {"DistrictID": "VDG", "DistrictName": "Vijaypura Division", "StateID": 29, "Latitude": 16.8302, "Longitude": 75.7100, "Population": 2170000},
]

ACTS = [
    {"ActID": 1, "ActName": "Indian Penal Code", "ActCode": "IPC", "Year": 1860},
    {"ActID": 2, "ActName": "Bharatiya Nyaya Sanhita", "ActCode": "BNS", "Year": 2023},
    {"ActID": 3, "ActName": "Narcotic Drugs and Psychotropic Substances Act", "ActCode": "NDPS", "Year": 1985},
    {"ActID": 4, "ActName": "Karnataka Prohibition Act", "ActCode": "KPA", "Year": 1961},
    {"ActID": 5, "ActName": "Information Technology Act", "ActCode": "IT", "Year": 2000},
    {"ActID": 6, "ActName": "Protection of Children from Sexual Offences Act", "ActCode": "POCSO", "Year": 2012},
    {"ActID": 7, "ActName": "Prevention of Corruption Act", "ActCode": "PCA", "Year": 1988},
    {"ActID": 8, "ActName": "Arms Act", "ActCode": "ARMS", "Year": 1959},
    {"ActID": 9, "ActName": "Scheduled Castes and Tribes Act", "ActCode": "SCST", "Year": 1989},
    {"ActID": 10, "ActName": "Motor Vehicles Act", "ActCode": "MVA", "Year": 1988},
]

SECTIONS = [
    {"SectionID": 1, "ActID": 1, "SectionNo": "302", "Description": "Punishment for murder", "MaxPunishment": "Death / Life"},
    {"SectionID": 2, "ActID": 1, "SectionNo": "376", "Description": "Punishment for rape", "MaxPunishment": "Rigorous imprisonment not less than 10 years"},
    {"SectionID": 3, "ActID": 1, "SectionNo": "379", "Description": "Punishment for theft", "MaxPunishment": "3 years"},
    {"SectionID": 4, "ActID": 1, "SectionNo": "392", "Description": "Punishment for robbery", "MaxPunishment": "10 years"},
    {"SectionID": 5, "ActID": 1, "SectionNo": "420", "Description": "Cheating and dishonestly inducing delivery of property", "MaxPunishment": "7 years"},
    {"SectionID": 6, "ActID": 1, "SectionNo": "498A", "Description": "Cruelty by husband or his relatives", "MaxPunishment": "3 years"},
    {"SectionID": 7, "ActID": 1, "SectionNo": "304", "Description": "Culpable homicide not amounting to murder", "MaxPunishment": "10 years / Life"},
    {"SectionID": 8, "ActID": 1, "SectionNo": "307", "Description": "Attempt to murder", "MaxPunishment": "10 years / Life"},
    {"SectionID": 9, "ActID": 1, "SectionNo": "395", "Description": "Dacoity", "MaxPunishment": "10 years"},
    {"SectionID": 10, "ActID": 1, "SectionNo": "323", "Description": "Punishment for voluntarily causing hurt", "MaxPunishment": "1 year"},
    {"SectionID": 11, "ActID": 1, "SectionNo": "324", "Description": "Voluntarily causing hurt by dangerous weapons", "MaxPunishment": "3 years"},
    {"SectionID": 12, "ActID": 1, "SectionNo": "354", "Description": "Assault or criminal force to woman with intent to outrage her modesty", "MaxPunishment": "2 years"},
    {"SectionID": 13, "ActID": 1, "SectionNo": "406", "Description": "Punishment for criminal breach of trust", "MaxPunishment": "3 years"},
    {"SectionID": 14, "ActID": 1, "SectionNo": "409", "Description": "Criminal breach of trust by public servant", "MaxPunishment": "10 years / Life"},
    {"SectionID": 15, "ActID": 2, "SectionNo": "103", "Description": "Murder (BNS equivalent of IPC 302)", "MaxPunishment": "Death / Life"},
    {"SectionID": 16, "ActID": 3, "SectionNo": "20", "Description": "Production, manufacture, possession of narcotic drugs", "MaxPunishment": "Rigorous imprisonment 10-20 years"},
    {"SectionID": 17, "ActID": 5, "SectionNo": "66C", "Description": "Identity theft", "MaxPunishment": "3 years"},
    {"SectionID": 18, "ActID": 5, "SectionNo": "66D", "Description": "Cheating by personation using computer", "MaxPunishment": "3 years"},
    {"SectionID": 19, "ActID": 1, "SectionNo": "363", "Description": "Punishment for kidnapping", "MaxPunishment": "7 years"},
    {"SectionID": 20, "ActID": 1, "SectionNo": "366", "Description": "Kidnapping/abducting or inducing woman to compel her marriage", "MaxPunishment": "10 years"},
]

CRIME_HEADS = [
    {"CrimeHeadID": 1, "HeadName": "Crimes Against Body"},
    {"CrimeHeadID": 2, "HeadName": "Crimes Against Property"},
    {"CrimeHeadID": 3, "HeadName": "Crimes Against Women"},
    {"CrimeHeadID": 4, "HeadName": "Crimes Against Children"},
    {"CrimeHeadID": 5, "HeadName": "Cyber Crimes"},
    {"CrimeHeadID": 6, "HeadName": "Drug Offences"},
    {"CrimeHeadID": 7, "HeadName": "Economic Crimes"},
    {"CrimeHeadID": 8, "HeadName": "Communal Offences"},
]

CRIME_SUB_HEADS = [
    {"CrimeSubHeadID": 1, "CrimeHeadID": 1, "SubHeadName": "Murder", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 2, "CrimeHeadID": 1, "SubHeadName": "Culpable Homicide", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 3, "CrimeHeadID": 1, "SubHeadName": "Attempt to Murder", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 4, "CrimeHeadID": 1, "SubHeadName": "Assault / Hurt", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 5, "CrimeHeadID": 2, "SubHeadName": "Theft", "GravityOffenceID": 3},
    {"CrimeSubHeadID": 6, "CrimeHeadID": 2, "SubHeadName": "Robbery", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 7, "CrimeHeadID": 2, "SubHeadName": "Dacoity", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 8, "CrimeHeadID": 2, "SubHeadName": "Burglary", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 9, "CrimeHeadID": 2, "SubHeadName": "Vehicle Theft", "GravityOffenceID": 3},
    {"CrimeSubHeadID": 10, "CrimeHeadID": 3, "SubHeadName": "Rape", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 11, "CrimeHeadID": 3, "SubHeadName": "Molestation", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 12, "CrimeHeadID": 3, "SubHeadName": "Cruelty by Husband", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 13, "CrimeHeadID": 3, "SubHeadName": "Kidnapping of Women", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 14, "CrimeHeadID": 4, "SubHeadName": "Child Abuse (POCSO)", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 15, "CrimeHeadID": 4, "SubHeadName": "Kidnapping of Child", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 16, "CrimeHeadID": 5, "SubHeadName": "Cyber Fraud", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 17, "CrimeHeadID": 5, "SubHeadName": "Identity Theft", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 18, "CrimeHeadID": 5, "SubHeadName": "Online Harassment", "GravityOffenceID": 3},
    {"CrimeSubHeadID": 19, "CrimeHeadID": 6, "SubHeadName": "Drug Possession", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 20, "CrimeHeadID": 6, "SubHeadName": "Drug Trafficking", "GravityOffenceID": 1},
    {"CrimeSubHeadID": 21, "CrimeHeadID": 7, "SubHeadName": "Cheating / Fraud", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 22, "CrimeHeadID": 7, "SubHeadName": "Criminal Breach of Trust", "GravityOffenceID": 2},
    {"CrimeSubHeadID": 23, "CrimeHeadID": 8, "SubHeadName": "Communal Violence", "GravityOffenceID": 1},
]

RANKS = [
    {"RankID": 1, "RankName": "Director General of Police", "RankCode": "DGP"},
    {"RankID": 2, "RankName": "Additional Director General", "RankCode": "ADGP"},
    {"RankID": 3, "RankName": "Inspector General", "RankCode": "IG"},
    {"RankID": 4, "RankName": "Deputy Inspector General", "RankCode": "DIG"},
    {"RankID": 5, "RankName": "Superintendent of Police", "RankCode": "SP"},
    {"RankID": 6, "RankName": "Additional SP", "RankCode": "ASP"},
    {"RankID": 7, "RankName": "Deputy SP", "RankCode": "DSP"},
    {"RankID": 8, "RankName": "Circle Inspector", "RankCode": "CI"},
    {"RankID": 9, "RankName": "Sub-Inspector", "RankCode": "SI"},
    {"RankID": 10, "RankName": "Assistant Sub-Inspector", "RankCode": "ASI"},
    {"RankID": 11, "RankName": "Head Constable", "RankCode": "HC"},
    {"RankID": 12, "RankName": "Police Constable", "RankCode": "PC"},
]

GRAVITY_OFFENCES = [
    {"GravityOffenceID": 1, "Description": "Heinous Offence", "Priority": "CRITICAL"},
    {"GravityOffenceID": 2, "Description": "Serious Offence", "Priority": "HIGH"},
    {"GravityOffenceID": 3, "Description": "Other Cognizable Offence", "Priority": "MEDIUM"},
    {"GravityOffenceID": 4, "Description": "Non-Cognizable Offence", "Priority": "LOW"},
]


def seed_table(table_name, rows):
    if MOCK:
        logger.info(f"[MOCK] Would seed {len(rows)} rows into {table_name}")
        return
    table = ds.table(table_name)
    count = 0
    for row in rows:
        try:
            table.insert_row(row)
            count += 1
            time.sleep(0.05)
        except Exception as e:
            logger.warning(f"  Skip {table_name} row {row}: {e}")
    logger.info(f"  Seeded {count}/{len(rows)} rows into {table_name}")


def main():
    logger.info("=== KAVERI Reference Data Seed ===")
    seed_table("State", STATES)
    seed_table("District", DISTRICTS)
    seed_table("Act", ACTS)
    seed_table("Section", SECTIONS)
    seed_table("CrimeHead", CRIME_HEADS)
    seed_table("CrimeSubHead", CRIME_SUB_HEADS)
    seed_table("Rank", RANKS)
    seed_table("GravityOffence", GRAVITY_OFFENCES)
    logger.info("=== Reference data seeding complete ===")


if __name__ == "__main__":
    main()
