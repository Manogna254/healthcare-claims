with date_spine as (
    select generate_series(
        '2015-01-01'::date,
        '2026-12-31'::date,
        '1 day'::interval
    )::date as date_day
)
select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day,
    extract(quarter from date_day) as quarter,
    to_char(date_day, 'Month') as month_name,
    to_char(date_day, 'Day') as day_name
from date_spine