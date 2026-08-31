select
    patient_id,
    birth_date,
    gender,
    state,
    city
from {{ source('raw', 'raw_patients') }}