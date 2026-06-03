{{
    config(
        materialized='table',
        tags=['gold']
    )
}}

select
    p.state_code,
    p.provider_type,
    p.entity_type,
    count(distinct f.npi)                                       as provider_count,
    sum(f.tot_beneficiaries)                                    as total_beneficiaries,
    sum(f.tot_services)                                         as total_services,
    sum(f.tot_submitted_charge)                                 as total_submitted_charge,
    sum(f.tot_medicare_payment)                                 as total_medicare_payment,
    avg(f.tot_medicare_payment)                                 as avg_payment_per_provider,
    avg(f.payment_to_charge_ratio)                              as avg_payment_to_charge_ratio,
    avg(b.avg_age)                                              as avg_beneficiary_age,
    avg(b.avg_risk_score)                                       as avg_risk_score,
    avg(b.cc_diabetes_pct)                                      as avg_diabetes_prevalence,
    avg(b.cc_hypertension_pct)                                  as avg_hypertension_prevalence,
    avg(b.cc_depression_pct)                                    as avg_depression_prevalence,
    avg(b.cc_ischemic_heart_pct)                                as avg_ischemic_heart_prevalence,
    avg(b.dual_eligible_count * 1.0 / nullif(b.dual_eligible_count + b.non_dual_count, 0)) as avg_dual_eligible_rate
from {{ ref('fact_provider_utilization') }} f
inner join {{ ref('dim_provider') }} p
    on f.provider_key = p.provider_key
left join {{ ref('stg_provider_beneficiaries') }} b
    on f.npi = b.npi
group by 1, 2, 3
