{{
    config(
        materialized='table',
        tags=['gold']
    )
}}

select
    {{ dbt_utils.generate_surrogate_key(['npi']) }}     as provider_key,
    npi,
    last_org_name,
    first_name,
    middle_initial,
    credentials,
    entity_type,
    street_address_1,
    street_address_2,
    city,
    state_code,
    state_fips,
    zip_code,
    ruca_code,
    ruca_description,
    country,
    provider_type,
    is_medicare_participating
from {{ ref('stg_providers') }}
