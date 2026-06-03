{{
    config(
        materialized='view',
        tags=['silver']
    )
}}

select
    rndrng_npi                                          as npi,
    rndrng_prvdr_last_org_name                          as last_org_name,
    rndrng_prvdr_first_name                             as first_name,
    rndrng_prvdr_mi                                     as middle_initial,
    rndrng_prvdr_crdntls                                as credentials,
    case rndrng_prvdr_ent_cd
        when 'I' then 'Individual'
        when 'O' then 'Organization'
        else rndrng_prvdr_ent_cd
    end                                                 as entity_type,
    rndrng_prvdr_st1                                    as street_address_1,
    rndrng_prvdr_st2                                    as street_address_2,
    rndrng_prvdr_city                                   as city,
    rndrng_prvdr_state_abrvtn                           as state_code,
    rndrng_prvdr_state_fips                             as state_fips,
    rndrng_prvdr_zip5                                   as zip_code,
    try_cast(rndrng_prvdr_ruca as decimal(5,2))         as ruca_code,
    rndrng_prvdr_ruca_desc                              as ruca_description,
    rndrng_prvdr_cntry                                  as country,
    rndrng_prvdr_type                                   as provider_type,
    case rndrng_prvdr_mdcr_prtcptg_ind
        when 'Y' then true
        when 'N' then false
        else null
    end                                                 as is_medicare_participating
from {{ ref('brz_provider_claims') }}
