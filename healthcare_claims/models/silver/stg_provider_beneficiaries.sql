{{
    config(
        materialized='view',
        tags=['silver']
    )
}}

select
    rndrng_npi                                                  as npi,
    -- age
    try_cast(bene_avg_age as decimal(5,2))                      as avg_age,
    try_cast(bene_age_lt_65_cnt as integer)                     as age_lt_65_count,
    try_cast(bene_age_65_74_cnt as integer)                     as age_65_74_count,
    try_cast(bene_age_75_84_cnt as integer)                     as age_75_84_count,
    try_cast(bene_age_gt_84_cnt as integer)                     as age_gt_84_count,
    -- gender
    try_cast(bene_feml_cnt as integer)                          as female_count,
    try_cast(bene_male_cnt as integer)                          as male_count,
    -- race / ethnicity
    try_cast(bene_race_wht_cnt as integer)                      as race_white_count,
    try_cast(bene_race_black_cnt as integer)                    as race_black_count,
    try_cast(bene_race_api_cnt as integer)                      as race_api_count,
    try_cast(bene_race_hspnc_cnt as integer)                    as race_hispanic_count,
    try_cast(bene_race_natind_cnt as integer)                   as race_native_count,
    try_cast(bene_race_othr_cnt as integer)                     as race_other_count,
    -- dual eligibility (Medicare + Medicaid)
    try_cast(bene_dual_cnt as integer)                          as dual_eligible_count,
    try_cast(bene_ndual_cnt as integer)                         as non_dual_count,
    -- risk score
    try_cast(bene_avg_risk_scre as decimal(10,4))               as avg_risk_score,
    -- behavioral health chronic condition prevalence (%)
    try_cast(bene_cc_bh_adhd_othcd_v1_pct as decimal(7,4))     as cc_adhd_pct,
    try_cast(bene_cc_bh_alcohol_drug_v1_pct as decimal(7,4))    as cc_alcohol_drug_pct,
    try_cast(bene_cc_bh_tobacco_v1_pct as decimal(7,4))         as cc_tobacco_pct,
    try_cast(bene_cc_bh_alz_nonalzdem_v2_pct as decimal(7,4))  as cc_alzheimers_pct,
    try_cast(bene_cc_bh_anxiety_v1_pct as decimal(7,4))         as cc_anxiety_pct,
    try_cast(bene_cc_bh_bipolar_v1_pct as decimal(7,4))         as cc_bipolar_pct,
    try_cast(bene_cc_bh_mood_v2_pct as decimal(7,4))            as cc_mood_disorder_pct,
    try_cast(bene_cc_bh_depress_v1_pct as decimal(7,4))         as cc_depression_pct,
    try_cast(bene_cc_bh_pd_v1_pct as decimal(7,4))              as cc_personality_disorder_pct,
    try_cast(bene_cc_bh_ptsd_v1_pct as decimal(7,4))            as cc_ptsd_pct,
    try_cast(bene_cc_bh_schizo_othpsy_v1_pct as decimal(7,4))   as cc_schizophrenia_pct,
    -- physical health chronic condition prevalence (%)
    try_cast(bene_cc_ph_asthma_v2_pct as decimal(7,4))          as cc_asthma_pct,
    try_cast(bene_cc_ph_afib_v2_pct as decimal(7,4))            as cc_afib_pct,
    try_cast(bene_cc_ph_cancer6_v2_pct as decimal(7,4))         as cc_cancer_pct,
    try_cast(bene_cc_ph_ckd_v2_pct as decimal(7,4))             as cc_ckd_pct,
    try_cast(bene_cc_ph_copd_v2_pct as decimal(7,4))            as cc_copd_pct,
    try_cast(bene_cc_ph_diabetes_v2_pct as decimal(7,4))        as cc_diabetes_pct,
    try_cast(bene_cc_ph_hf_nonihd_v2_pct as decimal(7,4))       as cc_heart_failure_pct,
    try_cast(bene_cc_ph_hyperlipidemia_v2_pct as decimal(7,4))  as cc_hyperlipidemia_pct,
    try_cast(bene_cc_ph_hypertension_v2_pct as decimal(7,4))    as cc_hypertension_pct,
    try_cast(bene_cc_ph_ischemicheart_v2_pct as decimal(7,4))   as cc_ischemic_heart_pct,
    try_cast(bene_cc_ph_osteoporosis_v2_pct as decimal(7,4))    as cc_osteoporosis_pct,
    try_cast(bene_cc_ph_parkinson_v2_pct as decimal(7,4))       as cc_parkinsons_pct,
    try_cast(bene_cc_ph_arthritis_v2_pct as decimal(7,4))       as cc_arthritis_pct,
    try_cast(bene_cc_ph_stroke_tia_v2_pct as decimal(7,4))      as cc_stroke_pct
from {{ ref('brz_provider_claims') }}
