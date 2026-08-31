select
    patient_id,
    birth_date,
    gender,
    state,
    city,
    date_part('year', age(current_date, birth_date)) as age
from {{ ref('stg_patients') }}