from datetime import datetime, timedelta
from pathlib import Path
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_python_script(script_path: str) -> None:
    """
    Run a Python script from the project root.

    This lets Airflow execute our existing pipeline scripts without
    duplicating the transformation logic inside the DAG.
    """
    full_script_path = PROJECT_ROOT / script_path

    result = subprocess.run(
        ["python", str(full_script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"Script failed: {script_path}\n"
            f"Return code: {result.returncode}\n"
            f"Error: {result.stderr}"
        )


default_args = {
    "owner": "stemy",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="data_transformation_quality",
    description="Create Silver tables, Gold mart, and run data quality checks",
    default_args=default_args,
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    tags=["norway-energy", "transform", "quality"],
) as dag:

    create_silver_tables = PythonOperator(
        task_id="create_silver_tables",
        python_callable=run_python_script,
        op_kwargs={
            "script_path": "src/transform/create_silver_tables.py",
        },
    )

    create_gold_mart = PythonOperator(
        task_id="create_gold_mart",
        python_callable=run_python_script,
        op_kwargs={
            "script_path": "src/transform/create_gold_mart.py",
        },
    )

    run_data_quality_checks = PythonOperator(
        task_id="run_data_quality_checks",
        python_callable=run_python_script,
        op_kwargs={
            "script_path": "src/quality/check_data_quality.py",
        },
    )

    create_silver_tables >> create_gold_mart >> run_data_quality_checks