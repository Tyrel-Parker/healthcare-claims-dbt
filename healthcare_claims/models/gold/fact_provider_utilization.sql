{{
    config(
        materialized='table',
        tags=['gold'],
        cluster_by=['state_code', 'provider_type']
    )
}}

select
    {{ dbt_utils.generate_surrogate_key(['u.npi']) }}       as utilization_key,
    p.provider_key,
    u.npi,
    p.state_code,
    p.provider_type,
    p.entity_type,
    p.is_medicare_participating,
    -- overall
    u.tot_hcpcs_codes,
    u.tot_beneficiaries,
    u.tot_services,
    u.tot_submitted_charge,
    u.tot_medicare_allowed,
    u.tot_medicare_payment,
    u.tot_medicare_standardized,
    -- drug
    u.drug_suppression_flag,
    u.drug_hcpcs_codes,
    u.drug_beneficiaries,
    u.drug_services,
    u.drug_submitted_charge,
    u.drug_medicare_payment,
    -- medical (non-drug)
    u.med_suppression_flag,
    u.med_hcpcs_codes,
    u.med_beneficiaries,
    u.med_services,
    u.med_submitted_charge,
    u.med_medicare_payment,
    -- derived
    div0(u.tot_medicare_payment, nullif(u.tot_submitted_charge, 0))     as payment_to_charge_ratio,
    div0(u.drug_medicare_payment, nullif(u.tot_medicare_payment, 0))    as drug_payment_share
from {{ ref('stg_provider_utilization') }} u
inner join {{ ref('dim_provider') }} p
    on u.npi = p.npi
