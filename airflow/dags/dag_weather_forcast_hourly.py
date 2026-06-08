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
    dag_id="weather_forecast_hourly",
    description="Extract hourly weather forecast snapshots for Norwegian price-area cities",
    default_args=default_args,
    start_date=datetime(2026, 6, 8),
    schedule="@hourly",
    catchup=False,
    tags=["norway-energy", "extract", "weather"],
) as dag:

    extract_weather_forecast = PythonOperator(
        task_id="extract_weather_forecast",
        python_callable=run_python_script,
        op_kwargs={
            "script_path": "src/extract/extract_weather_forecast.py",
        },
    )

    extract_weather_forecast