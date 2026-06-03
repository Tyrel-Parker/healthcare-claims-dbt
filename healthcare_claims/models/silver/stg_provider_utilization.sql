{{
    config(
        materialized='view',
        tags=['silver']
    )
}}

select
    rndrng_npi                                              as npi,
    -- overall totals
    try_cast(tot_hcpcs_cds as integer)                      as tot_hcpcs_codes,
    try_cast(tot_benes as integer)                          as tot_beneficiaries,
    try_cast(tot_srvcs as decimal(18,2))                    as tot_services,
    try_cast(tot_sbmtd_chrg as decimal(18,2))               as tot_submitted_charge,
    try_cast(tot_mdcr_alowd_amt as decimal(18,2))           as tot_medicare_allowed,
    try_cast(tot_mdcr_pymt_amt as decimal(18,2))            as tot_medicare_payment,
    try_cast(tot_mdcr_stdzd_amt as decimal(18,2))           as tot_medicare_standardized,
    -- drug service totals (may be suppressed for small counts)
    drug_sprsn_ind                                          as drug_suppression_flag,
    try_cast(drug_tot_hcpcs_cds as integer)                 as drug_hcpcs_codes,
    try_cast(drug_tot_benes as integer)                     as drug_beneficiaries,
    try_cast(drug_tot_srvcs as decimal(18,2))               as drug_services,
    try_cast(drug_sbmtd_chrg as decimal(18,2))              as drug_submitted_charge,
    try_cast(drug_mdcr_alowd_amt as decimal(18,2))          as drug_medicare_allowed,
    try_cast(drug_mdcr_pymt_amt as decimal(18,2))           as drug_medicare_payment,
    try_cast(drug_mdcr_stdzd_amt as decimal(18,2))          as drug_medicare_standardized,
    -- medical (non-drug) service totals
    med_sprsn_ind                                           as med_suppression_flag,
    try_cast(med_tot_hcpcs_cds as integer)                  as med_hcpcs_codes,
    try_cast(med_tot_benes as integer)                      as med_beneficiaries,
    try_cast(med_tot_srvcs as decimal(18,2))                as med_services,
    try_cast(med_sbmtd_chrg as decimal(18,2))               as med_submitted_charge,
    try_cast(med_mdcr_alowd_amt as decimal(18,2))           as med_medicare_allowed,
    try_cast(med_mdcr_pymt_amt as decimal(18,2))            as med_medicare_payment,
    try_cast(med_mdcr_stdzd_amt as decimal(18,2))           as med_medicare_standardized
from {{ ref('brz_provider_claims') }}
where try_cast(tot_benes as integer) is not null
