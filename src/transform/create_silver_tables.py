import json
from datetime import datetime
from pathlib import Path

import pandas as pd


# -----------------------------
# Configuration
# -----------------------------

BRONZE_ELECTRICITY_PATH = Path("data/bronze/electricity_prices")
BRONZE_WEATHER_PATH = Path("data/bronze/weather_forecast")
SILVER_PATH = Path("data/silver")

SILVER_ELECTRICITY_FILE = SILVER_PATH / "silver_electricity_prices.csv"
SILVER_WEATHER_FILE = SILVER_PATH / "silver_weather_forecast.csv"


# -----------------------------
# Helper functions
# -----------------------------

def read_json(file_path: Path) -> dict:
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_get(dictionary: dict, *keys):
    current_value = dictionary

    for key in keys:
        if not isinstance(current_value, dict):
            return None

        current_value = current_value.get(key)

        if current_value is None:
            return None

    return current_value


# -----------------------------
# Silver electricity table
# -----------------------------

def create_silver_electricity_prices() -> pd.DataFrame:
    """
    Read consolidated Bronze electricity JSON files and create a clean Silver table.

    New Bronze structure:
    data/bronze/electricity_prices/price_date=YYYY-MM-DD.json

    Inside each file:
    extraction_runs[] -> records[]
    """

    rows = []
    processed_at = datetime.now().isoformat(timespec="seconds")

    electricity_files = sorted(BRONZE_ELECTRICITY_PATH.glob("price_date=*.json"))

    if not electricity_files:
        raise FileNotFoundError(
            f"No consolidated electricity JSON files found in {BRONZE_ELECTRICITY_PATH}"
        )

    for file_path in electricity_files:
        bronze_data = read_json(file_path)

        price_date = bronze_data.get("price_date")
        extraction_runs = bronze_data.get("extraction_runs", [])

        for extraction_run in extraction_runs:
            extracted_at_raw = extraction_run.get("extracted_at_raw")
            extracted_date = extraction_run.get("extracted_date")
            extracted_time = extraction_run.get("extracted_time")
            records = extraction_run.get("records", [])

            for record in records:
                rows.append(
                    {
                        "source": bronze_data.get("source"),
                        "price_date": price_date,
                        "extracted_at_raw": extracted_at_raw,
                        "extracted_date": extracted_date,
                        "extracted_time": extracted_time,

                        "timestamp_start_raw": record.get("time_start_raw"),
                        "timestamp_end_raw": record.get("time_end_raw"),

                        "timestamp_start_local": record.get("time_start_raw"),
                        "timestamp_end_local": record.get("time_end_raw"),

                        "date": record.get("date"),
                        "time": record.get("start_time"),
                        "hour": record.get("hour"),
                        "hour_label": record.get("hour_label"),

                        "price_area": record.get("price_area"),
                        "price_area_name": record.get("price_area_name"),

                        "nok_per_kwh": record.get("NOK_per_kWh"),
                        "eur_per_kwh": record.get("EUR_per_kWh"),
                        "exchange_rate": record.get("EXR"),

                        "source_file": file_path.name,
                        "processed_at": processed_at,
                    }
                )

    df = pd.DataFrame(rows)

    # Convert datatypes
    df["timestamp_start_local"] = pd.to_datetime(df["timestamp_start_local"])
    df["timestamp_end_local"] = pd.to_datetime(df["timestamp_end_local"])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["hour"] = df["hour"].astype(int)

    df["nok_per_kwh"] = pd.to_numeric(df["nok_per_kwh"], errors="coerce")
    df["eur_per_kwh"] = pd.to_numeric(df["eur_per_kwh"], errors="coerce")
    df["exchange_rate"] = pd.to_numeric(df["exchange_rate"], errors="coerce")

    # If the same price_date was extracted more than once,
    # keep the latest extraction for each price_area/date/hour.
    df["extracted_at_sort"] = pd.to_datetime(df["extracted_at_raw"])

    df = df.sort_values("extracted_at_sort")

    df = df.drop_duplicates(
        subset=["price_area", "date", "hour"],
        keep="last",
    )

    df = df.drop(columns=["extracted_at_sort"])

    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    df.to_csv(SILVER_ELECTRICITY_FILE, index=False)

    print(f"Created {SILVER_ELECTRICITY_FILE}")
    print(f"Electricity rows: {len(df)}")

    return df


# -----------------------------
# Silver weather table
# -----------------------------

def create_silver_weather_forecast() -> pd.DataFrame:
    """
    Read consolidated Bronze weather JSON files and create a clean Silver table.

    New Bronze structure:
    data/bronze/weather_forecast/extraction_date=YYYY-MM-DD.json

    Inside each file:
    snapshots[] -> locations[] -> api_response -> properties -> timeseries[]
    """

    rows = []
    processed_at = datetime.now().isoformat(timespec="seconds")

    weather_files = sorted(BRONZE_WEATHER_PATH.glob("extraction_date=*.json"))

    if not weather_files:
        raise FileNotFoundError(
            f"No consolidated weather JSON files found in {BRONZE_WEATHER_PATH}"
        )

    for file_path in weather_files:
        bronze_data = read_json(file_path)

        extraction_date = bronze_data.get("extraction_date")
        snapshots = bronze_data.get("snapshots", [])

        for snapshot in snapshots:
            extracted_at_raw = snapshot.get("extracted_at_raw")
            extracted_date = snapshot.get("extracted_date")
            extracted_time = snapshot.get("extracted_time")
            extracted_hour = snapshot.get("extracted_hour")

            locations = snapshot.get("locations", [])

            for location in locations:
                price_area = location.get("price_area")
                city = location.get("city")
                latitude = location.get("latitude")
                longitude = location.get("longitude")

                api_response = location.get("api_response", {})

                weather_updated_at_utc = safe_get(
                    api_response,
                    "properties",
                    "meta",
                    "updated_at",
                )

                timeseries = safe_get(
                    api_response,
                    "properties",
                    "timeseries",
                ) or []

                for item in timeseries:
                    instant_details = safe_get(
                        item,
                        "data",
                        "instant",
                        "details",
                    ) or {}

                    precipitation_next_1h_mm = safe_get(
                        item,
                        "data",
                        "next_1_hours",
                        "details",
                        "precipitation_amount",
                    )

                    weather_symbol_next_1h = safe_get(
                        item,
                        "data",
                        "next_1_hours",
                        "summary",
                        "symbol_code",
                    )

                    precipitation_next_6h_mm = safe_get(
                        item,
                        "data",
                        "next_6_hours",
                        "details",
                        "precipitation_amount",
                    )

                    weather_symbol_next_6h = safe_get(
                        item,
                        "data",
                        "next_6_hours",
                        "summary",
                        "symbol_code",
                    )

                    weather_symbol_next_12h = safe_get(
                        item,
                        "data",
                        "next_12_hours",
                        "summary",
                        "symbol_code",
                    )

                    rows.append(
                        {
                            "source": bronze_data.get("source"),
                            "extraction_date": extraction_date,
                            "extracted_at_raw": extracted_at_raw,
                            "extracted_date": extracted_date,
                            "extracted_time": extracted_time,
                            "extracted_hour": extracted_hour,

                            "forecast_time_raw": item.get("forecast_time_raw") or item.get("time"),
                            "forecast_time_utc": item.get("forecast_time_raw") or item.get("time"),
                            "forecast_time_local": item.get("forecast_time_local"),

                            "date": item.get("local_date"),
                            "time": item.get("local_time"),
                            "hour": item.get("local_hour"),
                            "hour_label": item.get("local_hour_label"),
                            "price_area": price_area,
                            "city": city,
                            "latitude": latitude,
                            "longitude": longitude,

                            "weather_updated_at_utc": weather_updated_at_utc,

                            "air_temperature_celsius": instant_details.get("air_temperature"),
                            "wind_speed_mps": instant_details.get("wind_speed"),
                            "wind_from_direction_degrees": instant_details.get("wind_from_direction"),
                            "cloud_area_fraction_pct": instant_details.get("cloud_area_fraction"),
                            "relative_humidity_pct": instant_details.get("relative_humidity"),
                            "air_pressure_hpa": instant_details.get("air_pressure_at_sea_level"),

                            "precipitation_next_1h_mm": precipitation_next_1h_mm,
                            "weather_symbol_next_1h": weather_symbol_next_1h,
                            "precipitation_next_6h_mm": precipitation_next_6h_mm,
                            "weather_symbol_next_6h": weather_symbol_next_6h,
                            "weather_symbol_next_12h": weather_symbol_next_12h,

                            "source_file": file_path.name,
                            "processed_at": processed_at,
                        }
                    )

    df = pd.DataFrame(rows)

    # Fix time column safely.
    # In our enriched Bronze weather rows, the local readable time is stored in item["time"].
    # But the raw API also has item["time"], so we use forecast_time_local to derive it again.
    df["forecast_time_utc"] = pd.to_datetime(df["forecast_time_utc"], utc=True)
    df["forecast_time_local"] = pd.to_datetime(df["forecast_time_local"])

    df["date"] = df["forecast_time_local"].dt.date
    df["time"] = df["forecast_time_local"].dt.strftime("%H:%M:%S")
    df["hour"] = df["forecast_time_local"].dt.hour.astype(int)

    df["air_temperature_celsius"] = pd.to_numeric(
        df["air_temperature_celsius"],
        errors="coerce",
    )
    df["wind_speed_mps"] = pd.to_numeric(
        df["wind_speed_mps"],
        errors="coerce",
    )
    df["wind_from_direction_degrees"] = pd.to_numeric(
        df["wind_from_direction_degrees"],
        errors="coerce",
    )
    df["cloud_area_fraction_pct"] = pd.to_numeric(
        df["cloud_area_fraction_pct"],
        errors="coerce",
    )
    df["relative_humidity_pct"] = pd.to_numeric(
        df["relative_humidity_pct"],
        errors="coerce",
    )
    df["air_pressure_hpa"] = pd.to_numeric(
        df["air_pressure_hpa"],
        errors="coerce",
    )
    df["precipitation_next_1h_mm"] = pd.to_numeric(
        df["precipitation_next_1h_mm"],
        errors="coerce",
    )
    df["precipitation_next_6h_mm"] = pd.to_numeric(
        df["precipitation_next_6h_mm"],
        errors="coerce",
    )

    # Since weather can be collected multiple times per day,
    # keep the latest extraction for each price_area/date/hour.
    df["extracted_at_sort"] = pd.to_datetime(df["extracted_at_raw"])

    df = df.sort_values("extracted_at_sort")

    df = df.drop_duplicates(
        subset=["price_area", "date", "hour"],
        keep="last",
    )

    df = df.drop(columns=["extracted_at_sort"])

    SILVER_PATH.mkdir(parents=True, exist_ok=True)
    df.to_csv(SILVER_WEATHER_FILE, index=False)

    print(f"Created {SILVER_WEATHER_FILE}")
    print(f"Weather rows: {len(df)}")

    return df


# -----------------------------
# Main
# -----------------------------

def main() -> None:
    print("Starting Silver transformation...")

    create_silver_electricity_prices()
    create_silver_weather_forecast()

    print("Silver transformation completed.")


if __name__ == "__main__":
    main()