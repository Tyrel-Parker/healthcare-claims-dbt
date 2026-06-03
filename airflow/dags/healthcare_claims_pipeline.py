from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

DBT_DIR = "/home/tyrel/repos/healthcare-claims-dbt/healthcare_claims"
DBT_CMD = "/home/tyrel/repos/healthcare-claims-dbt/venv/bin/dbt"

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

    quality_check_raw = BashOperator(
        task_id="quality_check_raw",
        bash_command=(
            "snow sql "
            "--query \"CALL HEALTHCARE_CLAIMS.AUDIT.LOG_PIPELINE_QUALITY('BRONZE', 'PROVIDER_CLAIMS_RAW');\" "
            "--connection healthcare_admin"
        ),
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

    quality_check_bronze = BashOperator(
        task_id="quality_check_bronze",
        bash_command=(
            "snow sql "
            "--query \"CALL HEALTHCARE_CLAIMS.AUDIT.LOG_PIPELINE_QUALITY('BRONZE', 'BRZ_PROVIDER_CLAIMS');\" "
            "--connection healthcare_admin"
        ),
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
