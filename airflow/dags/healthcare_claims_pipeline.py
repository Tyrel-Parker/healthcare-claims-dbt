import yaml
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

DBT_DIR = "/home/tyrel/repos/healthcare-claims-dbt/healthcare_claims"
DBT_CMD = "/home/tyrel/repos/healthcare-claims-dbt/venv/bin/dbt"


def _load_sf_creds():
    profiles = yaml.safe_load(open(os.path.expanduser("~/.dbt/profiles.yml")))
    dev = profiles["healthcare_claims"]["outputs"]["dev"]
    return {
        "account":   dev["account"],
        "user":      dev["user"],
        "password":  dev["password"],
        "database":  dev["database"],
        "warehouse": dev["warehouse"],
        "role":      dev["role"],
    }


def call_quality_check(schema: str, table: str):
    import snowflake.connector
    creds = _load_sf_creds()
    conn = snowflake.connector.connect(**creds)
    cur = conn.cursor()
    cur.execute(
        f"CALL HEALTHCARE_CLAIMS.AUDIT.LOG_PIPELINE_QUALITY('{schema}', '{table}')"
    )
    result = cur.fetchone()[0]
    print(result)
    if result.startswith("WARNING"):
        raise ValueError(f"Quality check warning: {result}")


default_args = {
    "owner": "tyrel_parker",
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

with DAG(
    dag_id="healthcare_claims_pipeline",
    description="CMS provider claims: raw → bronze → silver → gold via dbt",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    tags=["healthcare", "claims", "dbt", "snowflake"],
) as dag:

    quality_check_raw = PythonOperator(
        task_id="quality_check_raw",
        python_callable=call_quality_check,
        op_kwargs={"schema": "BRONZE", "table": "PROVIDER_CLAIMS_RAW"},
    )

    dbt_run_bronze = BashOperator(
        task_id="dbt_run_bronze",
        bash_command=f"{DBT_CMD} run --select tag:bronze --project-dir {DBT_DIR} --profiles-dir ~/.dbt",
    )

    dbt_test_bronze = BashOperator(
        task_id="dbt_test_bronze",
        bash_command=f"{DBT_CMD} test --select tag:bronze --project-dir {DBT_DIR} --profiles-dir ~/.dbt",
    )

    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=f"{DBT_CMD} run --select tag:silver --project-dir {DBT_DIR} --profiles-dir ~/.dbt",
    )

    dbt_test_silver = BashOperator(
        task_id="dbt_test_silver",
        bash_command=f"{DBT_CMD} test --select tag:silver --project-dir {DBT_DIR} --profiles-dir ~/.dbt",
    )

    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command=f"{DBT_CMD} run --select tag:gold --project-dir {DBT_DIR} --profiles-dir ~/.dbt",
    )

    dbt_test_gold = BashOperator(
        task_id="dbt_test_gold",
        bash_command=f"{DBT_CMD} test --select tag:gold --project-dir {DBT_DIR} --profiles-dir ~/.dbt",
    )

    quality_check_bronze = PythonOperator(
        task_id="quality_check_bronze",
        python_callable=call_quality_check,
        op_kwargs={"schema": "BRONZE", "table": "BRZ_PROVIDER_CLAIMS"},
    )

    dbt_docs_generate = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"{DBT_CMD} docs generate --project-dir {DBT_DIR} --profiles-dir ~/.dbt",
    )

    (
        quality_check_raw
        >> dbt_run_bronze
        >> dbt_test_bronze
        >> dbt_run_silver
        >> dbt_test_silver
        >> dbt_run_gold
        >> dbt_test_gold
        >> quality_check_bronze
        >> dbt_docs_generate
    )
