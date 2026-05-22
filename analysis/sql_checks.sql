-- Health plan service operations inefficiency checks.
-- Table names mirror the synthetic CSVs in this public portfolio artifact.

with weekly_segment as (
    select
        segment_id,
        business_unit,
        week_start,
        contact_volume,
        contact_volume * avoidable_contact_rate as avoidable_contacts,
        repeat_contact_rate,
        sla_attainment,
        estimated_cost_leakage,
        utilization_exposure
    from weekly_operating_metrics
),

six_week_rollup as (
    select
        segment_id,
        business_unit,
        sum(contact_volume) as six_week_volume,
        sum(avoidable_contacts) as avoidable_contacts,
        avg(repeat_contact_rate) as repeat_contact_rate,
        avg(sla_attainment) as sla_attainment,
        sum(estimated_cost_leakage) as estimated_cost_leakage,
        sum(utilization_exposure) as utilization_exposure
    from weekly_segment
    where week_start >= dateadd(week, -6, current_date)
    group by 1, 2
)

select
    segment_id,
    business_unit,
    six_week_volume,
    avoidable_contacts,
    estimated_cost_leakage,
    utilization_exposure,
    case
        when avoidable_contacts / nullif(six_week_volume, 0) >= 0.35 then 'manager review'
        when repeat_contact_rate >= 0.18 then 'repeat-contact root cause'
        when sla_attainment < 0.80 then 'service level recovery'
        else 'monitor'
    end as recommended_follow_up
from six_week_rollup
order by estimated_cost_leakage + utilization_exposure desc;
