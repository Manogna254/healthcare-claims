select
    encounter_id,
    patient_id,
    start_date,
    end_date,
    encounter_class,
    reason_description
from {{ source('raw', 'raw_encounters') }}