select
    claim_id,
    patient_id,
    billable_start,
    total_amount,
    status,
    claim_type
from {{ source('raw', 'raw_claims') }}