select
    condition_id,
    patient_id,
    encounter_id,
    onset_date,
    code,
    description,
    clinical_status
from {{ source('raw', 'raw_conditions') }}