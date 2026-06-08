from datetime import datetime, timedelta
from pathlib import Path
import subprocess

from airflow import DAG
from airflow.operators.python import PythonOperator


PROJECT_ROOT = Path("/opt/airflow/project")


def run_python_script(script_path: str) -> None:
    """
    Run a Python script from the project root inside the Airflow Docker container.
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
    dag_id="electricity_prices_daily",
    description="Extract daily electricity prices for Norwegian price areas",
    default_args=default_args,
    start_date=datetime(2026, 6, 8),
    schedule="0 14 * * *",
    catchup=False,
    tags=["norway-energy", "extract", "electricity"],
) as dag:

    extract_electricity_prices = PythonOperator(
        task_id="extract_electricity_prices",
        python_callable=run_python_script,
        op_kwargs={
            "script_path": "src/extract/extract_electricity_prices.py",
        },
    )

    extract_electricity_prices