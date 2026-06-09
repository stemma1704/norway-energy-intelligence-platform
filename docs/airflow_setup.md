# Airflow Setup — Norway Energy Intelligence Platform

## 1. Purpose

This project uses **Apache Airflow** to orchestrate the Norway Energy data pipeline.

Airflow is responsible for running the pipeline tasks in the correct order and on a defined schedule.

The pipeline includes:

```text
Electricity API extraction
Weather API extraction
Silver transformation
Gold mart creation
Data quality checks
```

Airflow does not replace the Python scripts.
Instead, Airflow runs the existing Python scripts as scheduled tasks.

---

## 2. Why Airflow is used

Before Airflow, the pipeline scripts were run manually:

```bash
python src/extract/extract_electricity_prices.py
python src/extract/extract_weather_forecast.py
python src/transform/create_silver_tables.py
python src/transform/create_gold_mart.py
python src/quality/check_data_quality.py
```

With Airflow, these scripts can be:

* Scheduled
* Monitored
* Retried if they fail
* Run in the correct order
* Checked through the Airflow UI

This makes the project closer to a real data engineering workflow.

---

## 3. Airflow architecture

The local Airflow setup runs using Docker Compose.

The Docker setup starts the following services:

| Service             | Purpose                                                                              |
| ------------------- | ------------------------------------------------------------------------------------ |
| `postgres`          | Stores Airflow metadata such as DAG runs, task status, users, and scheduling history |
| `airflow-webserver` | Runs the Airflow web UI                                                              |
| `airflow-scheduler` | Reads DAG schedules and triggers tasks                                               |
| `airflow-init`      | Initializes the Airflow metadata database and creates the admin user                 |

The most important service for automatic scheduling is:

```text
airflow-scheduler
```

If the scheduler is not running, DAGs will not be triggered automatically.

---

## 4. Project structure

Airflow DAG files are stored in:

```text
airflow/dags/
```

Current DAG files:

```text
airflow/dags/dag_electricity_prices_daily.py
airflow/dags/dag_weather_forecast_hourly.py
airflow/dags/dag_data_transformation_quality.py
```

The actual pipeline logic is stored in:

```text
src/extract/
src/transform/
src/quality/
```

This separation is intentional.

The DAGs define **when and in what order** scripts run.
The Python scripts define **what work is done**.

---

## 5. How to start Airflow

From the project root, run:

```bash
docker compose up
```

This starts:

```text
postgres
airflow-webserver
airflow-scheduler
```

If you want to run Airflow in the background, use:

```bash
docker compose up -d
```

The `-d` means detached mode.

---

## 6. How to access Airflow UI

Open this URL in the browser:

```text
http://localhost:8081
```

Login:

```text
username: admin
password: admin
```

Port `8081` is used on the laptop because port `8080` may already be used by another local application.

Inside the container, Airflow still runs on port `8080`.

The Docker port mapping is:

```text
localhost:8081 → container:8080
```

---

## 7. Airflow DAGs

The project currently has three DAGs.

| DAG ID                        | Schedule       | Purpose                                                             |
| ----------------------------- | -------------- | ------------------------------------------------------------------- |
| `electricity_prices_daily`    | Daily at 14:00 | Extract electricity prices from the electricity API                 |
| `weather_forecast_hourly`     | Hourly         | Extract weather forecast snapshots from MET Norway                  |
| `data_transformation_quality` | Hourly         | Create Silver tables, create Gold mart, and run data quality checks |

---

## 8. DAG 1: Electricity prices daily

DAG file:

```text
airflow/dags/dag_electricity_prices_daily.py
```

DAG ID:

```text
electricity_prices_daily
```

This DAG runs:

```text
src/extract/extract_electricity_prices.py
```

The output is stored in:

```text
data/bronze/electricity_prices/
```

Example output:

```text
data/bronze/electricity_prices/price_date=2026-06-08.json
```

Schedule:

```text
0 14 * * *
```

This means:

```text
Run every day at 14:00
```

The electricity API script collects prices for today and tomorrow if available.

---

## 9. DAG 2: Weather forecast hourly

DAG file:

```text
airflow/dags/dag_weather_forecast_hourly.py
```

DAG ID:

```text
weather_forecast_hourly
```

This DAG runs:

```text
src/extract/extract_weather_forecast.py
```

The output is stored in:

```text
data/bronze/weather_forecast/
```

Example output:

```text
data/bronze/weather_forecast/extraction_date=2026-06-08.json
```

Schedule:

```text
@hourly
```

This means:

```text
Run once every hour
```

Weather data is collected as forecast snapshots.
Each hourly run appends a new snapshot to the daily weather Bronze JSON file.

---

## 10. DAG 3: Data transformation and quality

DAG file:

```text
airflow/dags/dag_data_transformation_quality.py
```

DAG ID:

```text
data_transformation_quality
```

This DAG runs the transformation and validation layer:

```text
create_silver_tables
        ↓
create_gold_mart
        ↓
run_data_quality_checks
```

It runs these scripts:

```text
src/transform/create_silver_tables.py
src/transform/create_gold_mart.py
src/quality/check_data_quality.py
```

The outputs are:

```text
data/silver/silver_electricity_prices.csv
data/silver/silver_weather_forecast.csv
data/gold/gold_price_weather_mart.csv
```

Schedule:

```text
@hourly
```

This means the transformation and quality checks run every hour while Airflow is running.

---

## 11. What happens if a task fails?

If a task fails, Airflow marks that task as failed.

For example:

```text
create_silver_tables failed
```

Then downstream tasks will not run.

In the transformation DAG:

```text
create_silver_tables
        ↓
create_gold_mart
        ↓
run_data_quality_checks
```

If `create_silver_tables` fails, then `create_gold_mart` and `run_data_quality_checks` will not run.

This protects the pipeline from creating Gold data from broken Silver data.

---

## 12. Retries

Each DAG uses retry settings.

Example:

```text
retries = 1
retry_delay = 5 minutes
```

This means if a task fails, Airflow will retry it once after 5 minutes.

Retries are useful because some failures are temporary, such as:

* API timeout
* Temporary network issue
* Short container issue

---

## 13. Catchup behavior

All DAGs use:

```text
catchup=False
```

This is important.

If Airflow is stopped for several hours, it will not automatically run all missed hourly schedules when restarted.

Example:

```text
Laptop off from 10:00 to 18:00
```

With `catchup=False`, Airflow will not run every missed weather extraction from 10:00, 11:00, 12:00, etc.

It will continue from the next scheduled run after Airflow is running again.

This is especially important for the weather DAG because the weather API provides current and future forecast snapshots, not historical observations.
