select
    c.claim_id,
    c.patient_id,
    c.billable_start::date as claim_date,
    c.total_amount,
    c.status,
    c.claim_type,
    p.gender as patient_gender,
    p.age as patient_age,
    p.state as patient_state
from {{ ref('stg_claims') }} c
left join {{ ref('dim_patients') }} p
    on c.patient_id = p.patient_id