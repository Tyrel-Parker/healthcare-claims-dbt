# Build Guide

Step-by-step instructions for standing up this pipeline from scratch, including the non-obvious configuration decisions that took trial and error to get right.

---

## Prerequisites

- Python 3.12+
- A Snowflake account (free trial works)
- Snowflake CLI (`snow` command) — [install guide](https://docs.snowflake.com/en/developer-guide/snowflake-cli/installation/installation)

---

## 1. Snowflake Setup

Run this as your admin user in a Snowflake worksheet.

```sql
-- Database and schemas
CREATE DATABASE HEALTHCARE_CLAIMS;
CREATE SCHEMA HEALTHCARE_CLAIMS.BRONZE;
CREATE SCHEMA HEALTHCARE_CLAIMS.SILVER;
CREATE SCHEMA HEALTHCARE_CLAIMS.GOLD;
CREATE SCHEMA HEALTHCARE_CLAIMS.AUDIT;

-- Warehouse (X-Small is plenty for dev; auto-suspend to avoid burning credits)
CREATE WAREHOUSE CLAIMS_DEV_WH
    WAREHOUSE_SIZE = 'X-SMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

-- Role for dbt — principle of least privilege
CREATE ROLE DBT_ROLE;
GRANT USAGE ON DATABASE HEALTHCARE_CLAIMS TO ROLE DBT_ROLE;
GRANT USAGE ON ALL SCHEMAS IN DATABASE HEALTHCARE_CLAIMS TO ROLE DBT_ROLE;
GRANT CREATE TABLE ON ALL SCHEMAS IN DATABASE HEALTHCARE_CLAIMS TO ROLE DBT_ROLE;
GRANT CREATE VIEW ON ALL SCHEMAS IN DATABASE HEALTHCARE_CLAIMS TO ROLE DBT_ROLE;
GRANT SELECT ON ALL TABLES IN DATABASE HEALTHCARE_CLAIMS TO ROLE DBT_ROLE;
GRANT USAGE ON WAREHOUSE CLAIMS_DEV_WH TO ROLE DBT_ROLE;

-- dbt service user
CREATE USER DBT_USER PASSWORD = '<your-password>' DEFAULT_ROLE = DBT_ROLE;
GRANT ROLE DBT_ROLE TO USER DBT_USER;
```

---

## 2. Create the Stage

A named stage is how Snowflake handles file uploads before loading. The `FILE_FORMAT` options here must match the COPY INTO command later.

```sql
USE DATABASE HEALTHCARE_CLAIMS;
USE SCHEMA BRONZE;

CREATE STAGE CMS_STAGE
    FILE_FORMAT = (
        TYPE = 'CSV'
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        SKIP_HEADER = 1
        NULL_IF = ('', 'NULL', 'N/A')
    );
```

---

## 3. Python Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install dbt-core dbt-snowflake
```

---

## 4. Configure dbt Profile

dbt profiles live at `~/.dbt/profiles.yml` (outside the project directory — never committed to git).

```yaml
healthcare_claims:
  outputs:
    dev:
      type: snowflake
      account: <your-account-identifier>   # e.g. dc45256.us-east-2.aws
      user: DBT_USER
      password: <your-dbt-user-password>
      role: DBT_ROLE
      database: HEALTHCARE_CLAIMS
      schema: BRONZE                        # default schema; overridden per-layer by dbt_project.yml
      warehouse: CLAIMS_DEV_WH
      threads: 4
  target: dev
```

Verify the connection:
```bash
cd healthcare_claims
dbt debug
```

---

## 5. Configure Snowflake CLI Connections

The Snowflake CLI (`snow`) is used for file uploads and admin SQL — separate from dbt. Run `snow connection add` and set up two connections:

- `healthcare` — DBT_USER / DBT_ROLE (for running dbt ops if needed)
- `healthcare_admin` — your admin user / ACCOUNTADMIN (for data loading and grants)

---

## 6. Upload the CMS Data File

```bash
snow stage copy \
  "/path/to/MUP_PHY_R26_P05_V10_D24_Prov.csv" \
  "@HEALTHCARE_CLAIMS.BRONZE.CMS_STAGE" \
  --connection healthcare_admin
```

**Note:** The 2024 "by Provider" file has 81 columns. The README from earlier versions of this project referenced 25 columns from the older "by Provider and Service" schema — those two datasets have completely different shapes.

---

## 7. Create the Raw Table and Load Data

The table must define all 81 columns as VARCHAR. Type casting happens in dbt, not here. This lets you reload raw data without touching the transformation logic.

```sql
USE DATABASE HEALTHCARE_CLAIMS;
USE SCHEMA BRONZE;
USE WAREHOUSE CLAIMS_DEV_WH;

CREATE TABLE IF NOT EXISTS PROVIDER_CLAIMS_RAW (
    RNDRNG_NPI VARCHAR, RNDRNG_PRVDR_LAST_ORG_NAME VARCHAR,
    RNDRNG_PRVDR_FIRST_NAME VARCHAR, RNDRNG_PRVDR_MI VARCHAR,
    RNDRNG_PRVDR_CRDNTLS VARCHAR, RNDRNG_PRVDR_ENT_CD VARCHAR,
    RNDRNG_PRVDR_ST1 VARCHAR, RNDRNG_PRVDR_ST2 VARCHAR,
    RNDRNG_PRVDR_CITY VARCHAR, RNDRNG_PRVDR_STATE_ABRVTN VARCHAR,
    RNDRNG_PRVDR_STATE_FIPS VARCHAR, RNDRNG_PRVDR_ZIP5 VARCHAR,
    RNDRNG_PRVDR_RUCA VARCHAR, RNDRNG_PRVDR_RUCA_DESC VARCHAR,
    RNDRNG_PRVDR_CNTRY VARCHAR, RNDRNG_PRVDR_TYPE VARCHAR,
    RNDRNG_PRVDR_MDCR_PRTCPTG_IND VARCHAR,
    TOT_HCPCS_CDS VARCHAR, TOT_BENES VARCHAR, TOT_SRVCS VARCHAR,
    TOT_SBMTD_CHRG VARCHAR, TOT_MDCR_ALOWD_AMT VARCHAR,
    TOT_MDCR_PYMT_AMT VARCHAR, TOT_MDCR_STDZD_AMT VARCHAR,
    DRUG_SPRSN_IND VARCHAR, DRUG_TOT_HCPCS_CDS VARCHAR,
    DRUG_TOT_BENES VARCHAR, DRUG_TOT_SRVCS VARCHAR,
    DRUG_SBMTD_CHRG VARCHAR, DRUG_MDCR_ALOWD_AMT VARCHAR,
    DRUG_MDCR_PYMT_AMT VARCHAR, DRUG_MDCR_STDZD_AMT VARCHAR,
    MED_SPRSN_IND VARCHAR, MED_TOT_HCPCS_CDS VARCHAR,
    MED_TOT_BENES VARCHAR, MED_TOT_SRVCS VARCHAR,
    MED_SBMTD_CHRG VARCHAR, MED_MDCR_ALOWD_AMT VARCHAR,
    MED_MDCR_PYMT_AMT VARCHAR, MED_MDCR_STDZD_AMT VARCHAR,
    BENE_AVG_AGE VARCHAR, BENE_AGE_LT_65_CNT VARCHAR,
    BENE_AGE_65_74_CNT VARCHAR, BENE_AGE_75_84_CNT VARCHAR,
    BENE_AGE_GT_84_CNT VARCHAR, BENE_FEML_CNT VARCHAR,
    BENE_MALE_CNT VARCHAR, BENE_RACE_WHT_CNT VARCHAR,
    BENE_RACE_BLACK_CNT VARCHAR, BENE_RACE_API_CNT VARCHAR,
    BENE_RACE_HSPNC_CNT VARCHAR, BENE_RACE_NATIND_CNT VARCHAR,
    BENE_RACE_OTHR_CNT VARCHAR, BENE_DUAL_CNT VARCHAR,
    BENE_NDUAL_CNT VARCHAR,
    BENE_CC_BH_ADHD_OTHCD_V1_PCT VARCHAR, BENE_CC_BH_ALCOHOL_DRUG_V1_PCT VARCHAR,
    BENE_CC_BH_TOBACCO_V1_PCT VARCHAR, BENE_CC_BH_ALZ_NONALZDEM_V2_PCT VARCHAR,
    BENE_CC_BH_ANXIETY_V1_PCT VARCHAR, BENE_CC_BH_BIPOLAR_V1_PCT VARCHAR,
    BENE_CC_BH_MOOD_V2_PCT VARCHAR, BENE_CC_BH_DEPRESS_V1_PCT VARCHAR,
    BENE_CC_BH_PD_V1_PCT VARCHAR, BENE_CC_BH_PTSD_V1_PCT VARCHAR,
    BENE_CC_BH_SCHIZO_OTHPSY_V1_PCT VARCHAR,
    BENE_CC_PH_ASTHMA_V2_PCT VARCHAR, BENE_CC_PH_AFIB_V2_PCT VARCHAR,
    BENE_CC_PH_CANCER6_V2_PCT VARCHAR, BENE_CC_PH_CKD_V2_PCT VARCHAR,
    BENE_CC_PH_COPD_V2_PCT VARCHAR, BENE_CC_PH_DIABETES_V2_PCT VARCHAR,
    BENE_CC_PH_HF_NONIHD_V2_PCT VARCHAR, BENE_CC_PH_HYPERLIPIDEMIA_V2_PCT VARCHAR,
    BENE_CC_PH_HYPERTENSION_V2_PCT VARCHAR, BENE_CC_PH_ISCHEMICHEART_V2_PCT VARCHAR,
    BENE_CC_PH_OSTEOPOROSIS_V2_PCT VARCHAR, BENE_CC_PH_PARKINSON_V2_PCT VARCHAR,
    BENE_CC_PH_ARTHRITIS_V2_PCT VARCHAR, BENE_CC_PH_STROKE_TIA_V2_PCT VARCHAR,
    BENE_AVG_RISK_SCRE VARCHAR
);

COPY INTO PROVIDER_CLAIMS_RAW
FROM @HEALTHCARE_CLAIMS.BRONZE.CMS_STAGE
FILE_FORMAT = (
    TYPE = 'CSV'
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    SKIP_HEADER = 1
    NULL_IF = ('', 'NULL', 'N/A')
)
ON_ERROR = 'CONTINUE';

SELECT COUNT(*) FROM PROVIDER_CLAIMS_RAW;  -- expect ~1,296,739
```

---

## 8. Install dbt Packages and Run

```bash
cd healthcare_claims
source ../venv/bin/activate

dbt deps          # installs dbt-utils
dbt run           # builds all 7 models in dependency order
dbt test          # runs 21 data quality tests
```

### The schema doubling problem

By default, dbt constructs a schema name by concatenating the profile's target schema with any custom schema you set in `dbt_project.yml`. So if your profile says `schema: BRONZE` and your model config says `+schema: BRONZE`, you get `BRONZE_BRONZE`.

The fix is a custom macro at `macros/generate_schema_name.sql` that makes the custom schema take full precedence:

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

This is [documented behavior](https://docs.getdbt.com/docs/build/custom-schemas#an-alternative-pattern-for-generating-schema-names) in dbt — it's just not the default.

### Granting access after dbt runs

Tables created by `DBT_USER`/`DBT_ROLE` aren't automatically accessible to `ACCOUNTADMIN` for data reads (admin privileges handle grants, not object access). After the first run, grant access:

```sql
GRANT SELECT ON ALL TABLES IN SCHEMA HEALTHCARE_CLAIMS.GOLD TO ROLE ACCOUNTADMIN;
GRANT SELECT ON ALL TABLES IN SCHEMA HEALTHCARE_CLAIMS.BRONZE TO ROLE ACCOUNTADMIN;
```

Or add a post-hook in `dbt_project.yml` to automate this on every run.

---

## 9. Generate dbt Docs

```bash
dbt docs generate
dbt docs serve
```

Opens a local web server at `http://localhost:8080` with the full lineage graph and column-level documentation.

---

## Notes on the IDE SQL linter

VS Code's SQL linter will flag every dbt file with errors like `Incorrect syntax near '{'`. These are false positives — the linter doesn't understand Jinja templating. The files are valid dbt SQL and compile correctly. Install the dbt Power User extension and set it as your SQL language handler for `.sql` files in the dbt project to get proper syntax highlighting.
