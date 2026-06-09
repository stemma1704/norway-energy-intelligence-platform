Norway Energy Intelligence Platform ⚡🌦️
1. Project Overview

The Norway Energy Intelligence Platform is a data engineering and analytics project that combines Norwegian electricity price data with weather forecast data.

The goal is to build a clean end-to-end pipeline that collects raw API data, transforms it into analytics-ready tables, validates data quality, and prepares a Gold dataset for Power BI reporting.

This project is designed as a portfolio project for data engineering, analytics engineering, and business intelligence roles.

2. Business Objective

Electricity prices in Norway vary by:

Price area
Date
Hour of the day
Market conditions
Weather conditions

This project helps answer questions such as:

Which electricity price area is the most expensive?
Which hours are cheapest or most expensive?
How do prices vary across NO1–NO5?
How does weather context such as temperature, wind, and precipitation relate to electricity prices?
Which hours may be better for flexible electricity usage such as EV charging or heating?
3. Tech Stack
Tool	Purpose
Python	API extraction, transformation, and quality checks
Pandas	Data cleaning and tabular transformation
Apache Airflow	Pipeline orchestration and scheduling
Docker Compose	Local Airflow environment
JSON	Bronze raw data storage
CSV	Silver and Gold local outputs
Git & GitHub	Version control and project portfolio
Power BI	Dashboard and reporting layer
4. Data Sources

This project uses two API sources.

Electricity Price API

The electricity API provides hourly electricity prices for Norwegian price areas.

Price areas used:

Price Area	Representative Region
NO1	Eastern Norway / Oslo
NO2	Southern Norway / Kristiansand
NO3	Central Norway / Trondheim
NO4	Northern Norway / Tromsø
NO5	Western Norway / Bergen

Main fields collected:

NOK_per_kWh
EUR_per_kWh
EXR
time_start
time_end
Weather Forecast API

The weather API provides forecast data for representative cities.

Price Area	City
NO1	Oslo
NO2	Kristiansand
NO3	Trondheim
NO4	Tromsø
NO5	Bergen

Main fields collected:

air_temperature
wind_speed
wind_from_direction
cloud_area_fraction
relative_humidity
air_pressure_at_sea_level
precipitation_amount
weather_symbol
5. Pipeline Architecture

The project follows a Bronze, Silver, and Gold architecture.

API Sources
    ↓
Bronze Layer
    ↓
Silver Layer
    ↓
Gold Layer
    ↓
Power BI Dashboard
Bronze Layer

The Bronze layer stores raw API data as JSON.

Electricity Bronze:

data/bronze/electricity_prices/price_date=YYYY-MM-DD.json

Weather Bronze:

data/bronze/weather_forecast/extraction_date=YYYY-MM-DD.json

The Bronze files preserve raw API timestamps and also include readable helper fields such as date, time, hour, and hour labels.

Silver Layer

The Silver layer converts raw JSON into clean tabular CSV files.

Outputs:

data/silver/silver_electricity_prices.csv
data/silver/silver_weather_forecast.csv

Silver includes:

Clean column names
Parsed timestamps
Local Norway time fields
Price area metadata
Weather variables
Source file and processed timestamp metadata
Gold Layer

The Gold layer joins electricity and weather data into a Power BI-ready mart.

Output:

data/gold/gold_price_weather_mart.csv

Join key:

price_area + date + hour

Gold includes dashboard-friendly fields such as:

date_label
day_name
month_name
hour_label
price_category
is_peak_price_hour
is_cheap_price_hour
daily_avg_price_nok_per_kwh
daily_min_price_nok_per_kwh
daily_max_price_nok_per_kwh
6. Airflow Orchestration

This project uses Apache Airflow with Docker Compose to orchestrate the pipeline.

There are three DAGs.

DAG ID	Schedule	Purpose
electricity_prices_daily	Daily at 14:00	Extract electricity price data
weather_forecast_hourly	Hourly	Extract weather forecast snapshots
data_transformation_quality	Hourly	Create Silver tables, create Gold mart, and run data quality checks

The DAG files are stored in:

airflow/dags/

Current DAG files:

airflow/dags/dag_electricity_prices_daily.py
airflow/dags/dag_weather_forecast_hourly.py
airflow/dags/dag_data_transformation_quality.py

The DAGs call the existing Python scripts instead of duplicating business logic inside Airflow.

7. Data Quality Checks

A dedicated data quality script validates the Silver and Gold outputs.

Script:

src/quality/check_data_quality.py

The quality checks validate:

Required files exist
Tables are not empty
Required columns are present
Critical columns do not contain null values
Price areas are valid: NO1–NO5
Hour values are between 0 and 23
Duplicate business keys are not present
Electricity row counts are valid
Weather values are within expected ranges
Gold data has a reasonable weather join completeness
Price category values are valid

The quality script does not silently clean or overwrite data.
It validates the data and raises errors when critical issues are found.

8. Project Structure
norway_energy/
├── airflow/
│   └── dags/
│       ├── dag_electricity_prices_daily.py
│       ├── dag_weather_forecast_hourly.py
│       └── dag_data_transformation_quality.py
│
├── data/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── docs/
│   ├── data_dictionary.md
│   └── airflow_setup.md
│
├── src/
│   ├── extract/
│   │   ├── extract_electricity_prices.py
│   │   └── extract_weather_forecast.py
│   │
│   ├── transform/
│   │   ├── create_silver_tables.py
│   │   └── create_gold_mart.py
│   │
│   └── quality/
│       └── check_data_quality.py
│
├── docker-compose.yaml
├── requirements.txt
├── README.md
└── .gitignore
9. How to Run Locally Without Airflow

Activate the local Python environment and run the scripts manually from the project root.

python src/extract/extract_electricity_prices.py
python src/extract/extract_weather_forecast.py
python src/transform/create_silver_tables.py
python src/transform/create_gold_mart.py
python src/quality/check_data_quality.py

Manual run order:

Extract electricity data
Extract weather data
Create Silver tables
Create Gold mart
Run data quality checks
10. How to Run with Airflow

Start Airflow using Docker Compose:

docker compose up -d

Open the Airflow UI:

http://localhost:8081

Login:

username: admin
password: admin

For a full manual Airflow test, trigger DAGs in this order:

1. electricity_prices_daily
2. weather_forecast_hourly
3. data_transformation_quality

To stop Airflow:

docker compose down

Do not run this unless you intentionally want to reset Airflow metadata:

docker compose down -v