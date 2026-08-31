"""
Loads Synthea-generated FHIR JSON bundles into raw staging tables in Postgres.
Extracts Patient, Encounter, Condition, and Claim/ExplanationOfBenefit resources.
"""

import json
import os
import psycopg2
from psycopg2.extras import execute_values

# ---- CONNECTION SETTINGS ----
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "health_care",
    "user": "postgres",
    "password": os.environ.get("PGPASSWORD", ""),  
}

FHIR_DIR = os.path.join("synthea", "output", "fhir")

# ---- TABLE CREATION ----
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS raw_patients (
    patient_id TEXT PRIMARY KEY,
    birth_date DATE,
    gender TEXT,
    race TEXT,
    ethnicity TEXT,
    state TEXT,
    city TEXT
);

CREATE TABLE IF NOT EXISTS raw_encounters (
    encounter_id TEXT PRIMARY KEY,
    patient_id TEXT,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    encounter_class TEXT,
    reason_description TEXT
);

CREATE TABLE IF NOT EXISTS raw_conditions (
    condition_id TEXT PRIMARY KEY,
    patient_id TEXT,
    encounter_id TEXT,
    onset_date TIMESTAMP,
    code TEXT,
    description TEXT,
    clinical_status TEXT
);

CREATE TABLE IF NOT EXISTS raw_claims (
    claim_id TEXT PRIMARY KEY,
    patient_id TEXT,
    billable_start TIMESTAMP,
    total_amount NUMERIC,
    status TEXT,
    claim_type TEXT
);
"""

def get_ref_id(ref):
    """Extracts the ID portion from a FHIR reference string like 'Patient/abc-123'."""
    if not ref:
        return None
    return ref.split("/")[-1].split(":")[-1]

def parse_bundle(filepath, patients, encounters, conditions, claims):
    with open(filepath, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        rtype = resource.get("resourceType")

        if rtype == "Patient":
            patients.append((
                resource.get("id"),
                resource.get("birthDate"),
                (resource.get("gender") or "")[:50],
                (resource.get("extension", [{}])[0].get("valueString") if resource.get("extension") else None),
                None,  # ethnicity placeholder (varies by Synthea config)
                resource.get("address", [{}])[0].get("state") if resource.get("address") else None,
                resource.get("address", [{}])[0].get("city") if resource.get("address") else None,
            ))

        elif rtype == "Encounter":
            period = resource.get("period", {})
            encounters.append((
                resource.get("id"),
                get_ref_id(resource.get("subject", {}).get("reference")),
                period.get("start"),
                period.get("end"),
                resource.get("class", {}).get("code"),
                resource.get("reasonCode", [{}])[0].get("text") if resource.get("reasonCode") else None,
            ))

        elif rtype == "Condition":
            code_info = resource.get("code", {}).get("coding", [{}])
            conditions.append((
                resource.get("id"),
                get_ref_id(resource.get("subject", {}).get("reference")),
                get_ref_id(resource.get("encounter", {}).get("reference")),
                resource.get("onsetDateTime"),
                code_info[0].get("code") if code_info else None,
                code_info[0].get("display") if code_info else None,
                resource.get("clinicalStatus", {}).get("coding", [{}])[0].get("code") if resource.get("clinicalStatus") else None,
            ))

        elif rtype in ("Claim", "ExplanationOfBenefit"):
            total = resource.get("total", {})
            if isinstance(total, dict):
                amount = total.get("value")
            else:
                amount = None
            claims.append((
                resource.get("id"),
                get_ref_id(resource.get("patient", {}).get("reference")),
                resource.get("billablePeriod", {}).get("start"),
                amount,
                resource.get("status"),
                rtype,
            ))

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(CREATE_TABLES_SQL)
    conn.commit()

    patients, encounters, conditions, claims = [], [], [], []

    files = [f for f in os.listdir(FHIR_DIR) if f.endswith(".json")]
    print(f"Found {len(files)} FHIR files. Parsing...")

    for i, fname in enumerate(files, 1):
        parse_bundle(os.path.join(FHIR_DIR, fname), patients, encounters, conditions, claims)
        if i % 100 == 0:
            print(f"  processed {i}/{len(files)} files")

    print(f"Parsed: {len(patients)} patients, {len(encounters)} encounters, "
          f"{len(conditions)} conditions, {len(claims)} claims")

    if patients:
        execute_values(cur,
            "INSERT INTO raw_patients VALUES %s ON CONFLICT (patient_id) DO NOTHING", patients)
    if encounters:
        execute_values(cur,
            "INSERT INTO raw_encounters VALUES %s ON CONFLICT (encounter_id) DO NOTHING", encounters)
    if conditions:
        execute_values(cur,
            "INSERT INTO raw_conditions VALUES %s ON CONFLICT (condition_id) DO NOTHING", conditions)
    if claims:
        execute_values(cur,
            "INSERT INTO raw_claims VALUES %s ON CONFLICT (claim_id) DO NOTHING", claims)

    conn.commit()
    cur.close()
    conn.close()
    print("Done. Data loaded into healthcare_claims database.")

if __name__ == "__main__":
    main()