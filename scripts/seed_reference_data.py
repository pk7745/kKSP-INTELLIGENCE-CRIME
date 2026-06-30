"""
Seed script: Reference data — States, Districts, Units, Acts, Sections, Ranks,
CrimeHeads, CrimeSubHeads, GravityOffence, CaseCategory, CaseStatusMaster,
OccupationMaster, ReligionMaster, CasteMaster.
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
    {"StateID": 29, "StateName": "Karnataka", "NationalityID": 1, "Active": 1},
]

DISTRICTS = [
    {"DistrictID": "BEU", "DistrictName": "Bengaluru Urban",    "StateID": 29, "Active": 1},
    {"DistrictID": "BER", "DistrictName": "Bengaluru Rural",    "StateID": 29, "Active": 1},
    {"DistrictID": "MYS", "DistrictName": "Mysuru",             "StateID": 29, "Active": 1},
    {"DistrictID": "MNG", "DistrictName": "Mangaluru",          "StateID": 29, "Active": 1},
    {"DistrictID": "HUB", "DistrictName": "Hubballi-Dharwad",   "StateID": 29, "Active": 1},
    {"DistrictID": "BLG", "DistrictName": "Belagavi",           "StateID": 29, "Active": 1},
    {"DistrictID": "KLB", "DistrictName": "Kalaburagi",         "StateID": 29, "Active": 1},
    {"DistrictID": "DWD", "DistrictName": "Davanagere",         "StateID": 29, "Active": 1},
    {"DistrictID": "SHV", "DistrictName": "Shivamogga",         "StateID": 29, "Active": 1},
    {"DistrictID": "TUM", "DistrictName": "Tumakuru",           "StateID": 29, "Active": 1},
    {"DistrictID": "KOL", "DistrictName": "Kolar",              "StateID": 29, "Active": 1},
    {"DistrictID": "CHI", "DistrictName": "Chikkaballapur",     "StateID": 29, "Active": 1},
    {"DistrictID": "RAM", "DistrictName": "Ramanagara",         "StateID": 29, "Active": 1},
    {"DistrictID": "CKM", "DistrictName": "Chikkamagaluru",     "StateID": 29, "Active": 1},
    {"DistrictID": "HAS", "DistrictName": "Hassan",             "StateID": 29, "Active": 1},
    {"DistrictID": "MDY", "DistrictName": "Mandya",             "StateID": 29, "Active": 1},
    {"DistrictID": "CHN", "DistrictName": "Chamarajanagar",     "StateID": 29, "Active": 1},
    {"DistrictID": "KOD", "DistrictName": "Kodagu",             "StateID": 29, "Active": 1},
    {"DistrictID": "DKS", "DistrictName": "Dakshina Kannada",   "StateID": 29, "Active": 1},
    {"DistrictID": "UDU", "DistrictName": "Udupi",              "StateID": 29, "Active": 1},
    {"DistrictID": "UKN", "DistrictName": "Uttara Kannada",     "StateID": 29, "Active": 1},
    {"DistrictID": "GDA", "DistrictName": "Gadag",              "StateID": 29, "Active": 1},
    {"DistrictID": "DHR", "DistrictName": "Dharwad",            "StateID": 29, "Active": 1},
    {"DistrictID": "BPR", "DistrictName": "Bagalkot",           "StateID": 29, "Active": 1},
    {"DistrictID": "VJP", "DistrictName": "Vijayapura",         "StateID": 29, "Active": 1},
    {"DistrictID": "BDR", "DistrictName": "Bidar",              "StateID": 29, "Active": 1},
    {"DistrictID": "YDG", "DistrictName": "Yadgir",             "StateID": 29, "Active": 1},
    {"DistrictID": "RCH", "DistrictName": "Raichur",            "StateID": 29, "Active": 1},
    {"DistrictID": "KPN", "DistrictName": "Koppal",             "StateID": 29, "Active": 1},
    {"DistrictID": "BGT", "DistrictName": "Ballari",            "StateID": 29, "Active": 1},
    {"DistrictID": "CHD", "DistrictName": "Chitradurga",        "StateID": 29, "Active": 1},
    {"DistrictID": "TDV", "DistrictName": "Tumkur Division",    "StateID": 29, "Active": 1},
    {"DistrictID": "MYD", "DistrictName": "Mysuru Division",    "StateID": 29, "Active": 1},
    {"DistrictID": "RNG", "DistrictName": "Ramnagara",          "StateID": 29, "Active": 1},
    {"DistrictID": "CLG", "DistrictName": "Chikkamagalur",      "StateID": 29, "Active": 1},
    {"DistrictID": "BNP", "DistrictName": "Bidar North Patrol", "StateID": 29, "Active": 1},
    {"DistrictID": "VDG", "DistrictName": "Vijaypura Division", "StateID": 29, "Active": 1},
    {"DistrictID": "BMR", "DistrictName": "Bengaluru Metropolitan Range", "StateID": 29, "Active": 1},
]

# ── Acts ──────────────────────────────────────────────────────────────────────
# Per ER diagram: Act.ActCode (PK), ActDescription, ShortName, Active
ACTS = [
    {"ActCode": "IPC",   "ActDescription": "Indian Penal Code",                                    "ShortName": "IPC",   "Active": 1},
    {"ActCode": "BNS",   "ActDescription": "Bharatiya Nyaya Sanhita",                              "ShortName": "BNS",   "Active": 1},
    {"ActCode": "NDPS",  "ActDescription": "Narcotic Drugs and Psychotropic Substances Act",       "ShortName": "NDPS",  "Active": 1},
    {"ActCode": "KPA",   "ActDescription": "Karnataka Prohibition Act",                            "ShortName": "KPA",   "Active": 1},
    {"ActCode": "IT",    "ActDescription": "Information Technology Act",                           "ShortName": "IT",    "Active": 1},
    {"ActCode": "POCSO", "ActDescription": "Protection of Children from Sexual Offences Act",      "ShortName": "POCSO", "Active": 1},
    {"ActCode": "PCA",   "ActDescription": "Prevention of Corruption Act",                         "ShortName": "PCA",   "Active": 1},
    {"ActCode": "ARMS",  "ActDescription": "Arms Act",                                             "ShortName": "ARMS",  "Active": 1},
    {"ActCode": "SCST",  "ActDescription": "Scheduled Castes and Tribes Act",                      "ShortName": "SCST",  "Active": 1},
    {"ActCode": "MVA",   "ActDescription": "Motor Vehicles Act",                                   "ShortName": "MVA",   "Active": 1},
]

# ── Sections ──────────────────────────────────────────────────────────────────
# Per ER diagram: Section.ActCode (FK), SectionCode, SectionDescription, Active
SECTIONS = [
    {"ActCode": "IPC", "SectionCode": "302",  "SectionDescription": "Punishment for murder",                                          "Active": 1},
    {"ActCode": "IPC", "SectionCode": "376",  "SectionDescription": "Punishment for rape",                                            "Active": 1},
    {"ActCode": "IPC", "SectionCode": "379",  "SectionDescription": "Punishment for theft",                                           "Active": 1},
    {"ActCode": "IPC", "SectionCode": "392",  "SectionDescription": "Punishment for robbery",                                         "Active": 1},
    {"ActCode": "IPC", "SectionCode": "420",  "SectionDescription": "Cheating and dishonestly inducing delivery of property",         "Active": 1},
    {"ActCode": "IPC", "SectionCode": "498A", "SectionDescription": "Cruelty by husband or his relatives",                            "Active": 1},
    {"ActCode": "IPC", "SectionCode": "304",  "SectionDescription": "Culpable homicide not amounting to murder",                      "Active": 1},
    {"ActCode": "IPC", "SectionCode": "307",  "SectionDescription": "Attempt to murder",                                              "Active": 1},
    {"ActCode": "IPC", "SectionCode": "395",  "SectionDescription": "Dacoity",                                                        "Active": 1},
    {"ActCode": "IPC", "SectionCode": "323",  "SectionDescription": "Punishment for voluntarily causing hurt",                        "Active": 1},
    {"ActCode": "IPC", "SectionCode": "324",  "SectionDescription": "Voluntarily causing hurt by dangerous weapons",                  "Active": 1},
    {"ActCode": "IPC", "SectionCode": "354",  "SectionDescription": "Assault or criminal force to woman with intent to outrage her modesty", "Active": 1},
    {"ActCode": "IPC", "SectionCode": "406",  "SectionDescription": "Punishment for criminal breach of trust",                        "Active": 1},
    {"ActCode": "IPC", "SectionCode": "409",  "SectionDescription": "Criminal breach of trust by public servant",                     "Active": 1},
    {"ActCode": "IPC", "SectionCode": "363",  "SectionDescription": "Punishment for kidnapping",                                      "Active": 1},
    {"ActCode": "IPC", "SectionCode": "366",  "SectionDescription": "Kidnapping/abducting or inducing woman to compel her marriage",  "Active": 1},
    {"ActCode": "BNS", "SectionCode": "103",  "SectionDescription": "Murder (BNS equivalent of IPC 302)",                             "Active": 1},
    {"ActCode": "NDPS","SectionCode": "20",   "SectionDescription": "Production, manufacture, possession of narcotic drugs",          "Active": 1},
    {"ActCode": "IT",  "SectionCode": "66C",  "SectionDescription": "Identity theft",                                                 "Active": 1},
    {"ActCode": "IT",  "SectionCode": "66D",  "SectionDescription": "Cheating by personation using computer",                         "Active": 1},
]

# ── CrimeHead ─────────────────────────────────────────────────────────────────
# Per ER diagram: CrimeHeadID (PK), CrimeGroupName, Active
CRIME_HEADS = [
    {"CrimeHeadID": 1, "CrimeGroupName": "Crimes Against Body",     "Active": 1},
    {"CrimeHeadID": 2, "CrimeGroupName": "Crimes Against Property", "Active": 1},
    {"CrimeHeadID": 3, "CrimeGroupName": "Crimes Against Women",    "Active": 1},
    {"CrimeHeadID": 4, "CrimeGroupName": "Crimes Against Children", "Active": 1},
    {"CrimeHeadID": 5, "CrimeGroupName": "Cyber Crimes",            "Active": 1},
    {"CrimeHeadID": 6, "CrimeGroupName": "Drug Offences",           "Active": 1},
    {"CrimeHeadID": 7, "CrimeGroupName": "Economic Crimes",         "Active": 1},
    {"CrimeHeadID": 8, "CrimeGroupName": "Communal Offences",       "Active": 1},
]

# ── CrimeSubHead ──────────────────────────────────────────────────────────────
# Per ER diagram: CrimeSubHeadID (PK), CrimeHeadID (FK), CrimeHeadName, SeqID, Active
CRIME_SUB_HEADS = [
    {"CrimeSubHeadID": 1,  "CrimeHeadID": 1, "CrimeHeadName": "Murder",              "SeqID": 1,  "Active": 1},
    {"CrimeSubHeadID": 2,  "CrimeHeadID": 1, "CrimeHeadName": "Culpable Homicide",   "SeqID": 2,  "Active": 1},
    {"CrimeSubHeadID": 3,  "CrimeHeadID": 1, "CrimeHeadName": "Attempt to Murder",   "SeqID": 3,  "Active": 1},
    {"CrimeSubHeadID": 4,  "CrimeHeadID": 1, "CrimeHeadName": "Assault / Hurt",      "SeqID": 4,  "Active": 1},
    {"CrimeSubHeadID": 5,  "CrimeHeadID": 2, "CrimeHeadName": "Theft",               "SeqID": 1,  "Active": 1},
    {"CrimeSubHeadID": 6,  "CrimeHeadID": 2, "CrimeHeadName": "Robbery",             "SeqID": 2,  "Active": 1},
    {"CrimeSubHeadID": 7,  "CrimeHeadID": 2, "CrimeHeadName": "Dacoity",             "SeqID": 3,  "Active": 1},
    {"CrimeSubHeadID": 8,  "CrimeHeadID": 2, "CrimeHeadName": "Burglary",            "SeqID": 4,  "Active": 1},
    {"CrimeSubHeadID": 9,  "CrimeHeadID": 2, "CrimeHeadName": "Vehicle Theft",       "SeqID": 5,  "Active": 1},
    {"CrimeSubHeadID": 10, "CrimeHeadID": 3, "CrimeHeadName": "Rape",                "SeqID": 1,  "Active": 1},
    {"CrimeSubHeadID": 11, "CrimeHeadID": 3, "CrimeHeadName": "Molestation",         "SeqID": 2,  "Active": 1},
    {"CrimeSubHeadID": 12, "CrimeHeadID": 3, "CrimeHeadName": "Cruelty by Husband",  "SeqID": 3,  "Active": 1},
    {"CrimeSubHeadID": 13, "CrimeHeadID": 3, "CrimeHeadName": "Kidnapping of Women", "SeqID": 4,  "Active": 1},
    {"CrimeSubHeadID": 14, "CrimeHeadID": 4, "CrimeHeadName": "Child Abuse (POCSO)", "SeqID": 1,  "Active": 1},
    {"CrimeSubHeadID": 15, "CrimeHeadID": 4, "CrimeHeadName": "Kidnapping of Child", "SeqID": 2,  "Active": 1},
    {"CrimeSubHeadID": 16, "CrimeHeadID": 5, "CrimeHeadName": "Cyber Fraud",         "SeqID": 1,  "Active": 1},
    {"CrimeSubHeadID": 17, "CrimeHeadID": 5, "CrimeHeadName": "Identity Theft",      "SeqID": 2,  "Active": 1},
    {"CrimeSubHeadID": 18, "CrimeHeadID": 5, "CrimeHeadName": "Online Harassment",   "SeqID": 3,  "Active": 1},
    {"CrimeSubHeadID": 19, "CrimeHeadID": 6, "CrimeHeadName": "Drug Possession",     "SeqID": 1,  "Active": 1},
    {"CrimeSubHeadID": 20, "CrimeHeadID": 6, "CrimeHeadName": "Drug Trafficking",    "SeqID": 2,  "Active": 1},
    {"CrimeSubHeadID": 21, "CrimeHeadID": 7, "CrimeHeadName": "Cheating / Fraud",    "SeqID": 1,  "Active": 1},
    {"CrimeSubHeadID": 22, "CrimeHeadID": 7, "CrimeHeadName": "Criminal Breach of Trust", "SeqID": 2, "Active": 1},
    {"CrimeSubHeadID": 23, "CrimeHeadID": 8, "CrimeHeadName": "Communal Violence",   "SeqID": 1,  "Active": 1},
]

# ── GravityOffence ────────────────────────────────────────────────────────────
# Per ER diagram: GravityOffenceID (PK), LookupValue, Active
GRAVITY_OFFENCES = [
    {"GravityOffenceID": 1, "LookupValue": "Heinous Offence",            "Active": 1},
    {"GravityOffenceID": 2, "LookupValue": "Serious Offence",            "Active": 1},
    {"GravityOffenceID": 3, "LookupValue": "Other Cognizable Offence",   "Active": 1},
    {"GravityOffenceID": 4, "LookupValue": "Non-Cognizable Offence",     "Active": 1},
]

# ── CaseCategory ──────────────────────────────────────────────────────────────
# Per ER diagram: CaseCategoryID (PK), LookupValue
# CrimeNo first digit codes: 1=FIR, 3=UDR, 4=PAR, 8=Zero FIR
CASE_CATEGORIES = [
    {"CaseCategoryID": 1, "LookupValue": "FIR"},
    {"CaseCategoryID": 3, "LookupValue": "UDR"},
    {"CaseCategoryID": 4, "LookupValue": "PAR"},
    {"CaseCategoryID": 8, "LookupValue": "Zero FIR"},
]

# ── CaseStatusMaster ──────────────────────────────────────────────────────────
# Per ER diagram: CaseStatusID (PK), CaseStatusName
CASE_STATUS_MASTER = [
    {"CaseStatusID": 1, "CaseStatusName": "Under Investigation"},
    {"CaseStatusID": 2, "CaseStatusName": "Charge Sheeted"},
    {"CaseStatusID": 3, "CaseStatusName": "Final Report Filed"},
    {"CaseStatusID": 4, "CaseStatusName": "Closed"},
    {"CaseStatusID": 5, "CaseStatusName": "Pending Trial"},
    {"CaseStatusID": 6, "CaseStatusName": "Convicted"},
    {"CaseStatusID": 7, "CaseStatusName": "Acquitted"},
]

# ── OccupationMaster ──────────────────────────────────────────────────────────
# Per ER diagram: OccupationID (PK), OccupationName
OCCUPATION_MASTER = [
    {"OccupationID": 1,  "OccupationName": "Farmer"},
    {"OccupationID": 2,  "OccupationName": "Government Employee"},
    {"OccupationID": 3,  "OccupationName": "Private Employee"},
    {"OccupationID": 4,  "OccupationName": "Businessman"},
    {"OccupationID": 5,  "OccupationName": "Student"},
    {"OccupationID": 6,  "OccupationName": "Labourer"},
    {"OccupationID": 7,  "OccupationName": "Driver"},
    {"OccupationID": 8,  "OccupationName": "Shopkeeper"},
    {"OccupationID": 9,  "OccupationName": "Homemaker"},
    {"OccupationID": 10, "OccupationName": "Unemployed"},
    {"OccupationID": 11, "OccupationName": "Self-Employed"},
    {"OccupationID": 12, "OccupationName": "Retired"},
]

# ── ReligionMaster ────────────────────────────────────────────────────────────
# Per ER diagram: ReligionID (PK), ReligionName
RELIGION_MASTER = [
    {"ReligionID": 1, "ReligionName": "Hindu"},
    {"ReligionID": 2, "ReligionName": "Muslim"},
    {"ReligionID": 3, "ReligionName": "Christian"},
    {"ReligionID": 4, "ReligionName": "Jain"},
    {"ReligionID": 5, "ReligionName": "Buddhist"},
    {"ReligionID": 6, "ReligionName": "Sikh"},
    {"ReligionID": 7, "ReligionName": "Other"},
]

# ── CasteMaster ───────────────────────────────────────────────────────────────
# Per ER diagram: caste_master_id (PK), caste_master_name
CASTE_MASTER = [
    {"caste_master_id": 1,  "caste_master_name": "General"},
    {"caste_master_id": 2,  "caste_master_name": "OBC"},
    {"caste_master_id": 3,  "caste_master_name": "SC"},
    {"caste_master_id": 4,  "caste_master_name": "ST"},
    {"caste_master_id": 5,  "caste_master_name": "Minority"},
    {"caste_master_id": 6,  "caste_master_name": "Other"},
]

# ── Ranks ─────────────────────────────────────────────────────────────────────
# Per ER diagram: RankID (PK), RankName, Hierarchy, Active
RANKS = [
    {"RankID": 1,  "RankName": "Director General of Police",  "Hierarchy": 1,  "Active": 1},
    {"RankID": 2,  "RankName": "Additional Director General", "Hierarchy": 2,  "Active": 1},
    {"RankID": 3,  "RankName": "Inspector General",           "Hierarchy": 3,  "Active": 1},
    {"RankID": 4,  "RankName": "Deputy Inspector General",    "Hierarchy": 4,  "Active": 1},
    {"RankID": 5,  "RankName": "Superintendent of Police",    "Hierarchy": 5,  "Active": 1},
    {"RankID": 6,  "RankName": "Additional SP",               "Hierarchy": 6,  "Active": 1},
    {"RankID": 7,  "RankName": "Deputy SP",                   "Hierarchy": 7,  "Active": 1},
    {"RankID": 8,  "RankName": "Circle Inspector",            "Hierarchy": 8,  "Active": 1},
    {"RankID": 9,  "RankName": "Sub-Inspector",               "Hierarchy": 9,  "Active": 1},
    {"RankID": 10, "RankName": "Assistant Sub-Inspector",     "Hierarchy": 10, "Active": 1},
    {"RankID": 11, "RankName": "Head Constable",              "Hierarchy": 11, "Active": 1},
    {"RankID": 12, "RankName": "Police Constable",            "Hierarchy": 12, "Active": 1},
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
    seed_table("State",            STATES)
    seed_table("District",         DISTRICTS)
    seed_table("Act",              ACTS)
    seed_table("Section",          SECTIONS)
    seed_table("CrimeHead",        CRIME_HEADS)
    seed_table("CrimeSubHead",     CRIME_SUB_HEADS)
    seed_table("GravityOffence",   GRAVITY_OFFENCES)
    seed_table("CaseCategory",     CASE_CATEGORIES)
    seed_table("CaseStatusMaster", CASE_STATUS_MASTER)
    seed_table("OccupationMaster", OCCUPATION_MASTER)
    seed_table("ReligionMaster",   RELIGION_MASTER)
    seed_table("CasteMaster",      CASTE_MASTER)
    seed_table("Rank",             RANKS)
    logger.info("=== Reference data seeding complete ===")


if __name__ == "__main__":
    main()
