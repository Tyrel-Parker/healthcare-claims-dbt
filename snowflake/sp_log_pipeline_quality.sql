-- Creates the QUALITY_LOG audit table and the LOG_PIPELINE_QUALITY stored procedure.
-- Run as ACCOUNTADMIN or any role with CREATE TABLE/PROCEDURE on AUDIT schema.
-- Usage: CALL HEALTHCARE_CLAIMS.AUDIT.LOG_PIPELINE_QUALITY('BRONZE', 'BRZ_PROVIDER_CLAIMS');

USE DATABASE HEALTHCARE_CLAIMS;
USE SCHEMA AUDIT;
USE WAREHOUSE CLAIMS_DEV_WH;

CREATE TABLE IF NOT EXISTS QUALITY_LOG (
    log_id              INTEGER AUTOINCREMENT PRIMARY KEY,
    schema_name         VARCHAR,
    table_name          VARCHAR,
    row_count           INTEGER,
    null_npi_count      INTEGER,
    suppressed_drug_cnt INTEGER,
    suppressed_med_cnt  INTEGER,
    run_status          VARCHAR,
    message             VARCHAR,
    logged_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE PROCEDURE LOG_PIPELINE_QUALITY(P_SCHEMA VARCHAR, P_TABLE VARCHAR)
RETURNS VARCHAR
LANGUAGE JAVASCRIPT
AS
$$
    function queryScalar(conn, sql) {
        var stmt = conn.execute({sqlText: sql});
        stmt.next();
        return stmt.getColumnValue(1);
    }

    var base = 'HEALTHCARE_CLAIMS.' + P_SCHEMA + '.' + P_TABLE;

    var rowCount   = queryScalar(snowflake, 'SELECT COUNT(*) FROM ' + base);
    var nullNpi    = queryScalar(snowflake, "SELECT COUNT(*) FROM " + base + " WHERE RNDRNG_NPI IS NULL");
    var drugSuppr  = queryScalar(snowflake, "SELECT COUNT(*) FROM " + base + " WHERE DRUG_SPRSN_IND = '*'");
    var medSuppr   = queryScalar(snowflake, "SELECT COUNT(*) FROM " + base + " WHERE MED_SPRSN_IND = '*'");

    var status, message;
    if (nullNpi > 0) {
        status  = 'WARNING';
        message = 'Null NPIs: ' + nullNpi + ' | Drug suppressed: ' + drugSuppr + ' | Med suppressed: ' + medSuppr + ' | Total rows: ' + rowCount;
    } else {
        status  = 'PASSED';
        message = 'Total rows: ' + rowCount + ' | Drug suppressed: ' + drugSuppr + ' | Med suppressed: ' + medSuppr;
    }

    snowflake.execute({
        sqlText: `INSERT INTO HEALTHCARE_CLAIMS.AUDIT.QUALITY_LOG
                    (schema_name, table_name, row_count, null_npi_count, suppressed_drug_cnt, suppressed_med_cnt, run_status, message)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
        binds: [P_SCHEMA, P_TABLE, rowCount, nullNpi, drugSuppr, medSuppr, status, message]
    });

    return status + ': ' + message;
$$;
