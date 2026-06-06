import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd


# -----------------------------
# Configuration
# -----------------------------

NORWAY_TIMEZONE = ZoneInfo("Europe/Oslo")

BRONZE_ELECTRICITY_PATH = Path("data/bronze/electricity_prices")
BRONZE_WEATHER_PATH = Path("data/bronze/weather_forecast")

SILVER_PATH = Path("data/silver")

PRICE_AREA_NAMES = {
    "NO1": "Eastern Norway / Oslo",
    "NO2": "Southern Norway / Kristiansand",
    "NO3": "Central Norway / Trondheim",
    "NO4": "Northern Norway / Tromsø",
    "NO5": "Western Norway / Bergen",
}

WEATHER_LOCATIONS = {
    "NO1": {"city": "Oslo", "lat": 59.9139, "lon": 10.7522},
    "NO2": {"city": "Kristiansand", "lat": 58.1467, "lon": 7.9956},
    "NO3": {"city": "Trondheim", "lat": 63.4305, "lon": 10.3951},
    "NO4": {"city": "Tromsø", "lat": 69.6492, "lon": 18.9553},
    "NO5": {"city": "Bergen", "lat": 60.3913, "lon": 5.3221},
}


# -----------------------------
# Helper functions
# -----------------------------

def read_json(file_path: Path):
    """
    Read a JSON file and return Python data.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def safe_get(dictionary: dict, *keys):
    """
    Safely read a deeply nested dictionary.

    Example:
    safe_get(item, "data", "instant", "details", "air_temperature")

    If any key is missing, it returns None instead of crashing.
    """
    current_value = dictionary

    for key in keys:
        if not isinstance(current_value, dict):
            return None

        current_value = current_value.get(key)

        if current_value is None:
            return None

    return current_value


def create_hour_label(start_timestamp, end_timestamp) -> str:
    """
    Create readable hourly label such as:
    00:00 - 01:00
    """
    start_time = start_timestamp.strftime("%H:%M")
    end_time = end_timestamp.strftime("%H:%M")
    return f"{start_time} - {end_time}"


# -----------------------------
# Silver electricity table
# -----------------------------

def create_silver_electricity_prices() -> pd.DataFrame:
    """
    Convert raw electricity price JSON files into a clean Silver table.

    Input:
    data/bronze/electricity_prices/*.json

    Output:
    data/silver/silver_electricity_prices.csv
    """

    rows = []
    processed_at = datetime.now().isoformat(timespec="seconds")

    electricity_files = sorted(BRONZE_ELECTRICITY_PATH.glob("*.json"))

    if not electricity_files:
        raise FileNotFoundError(
            f"No electricity JSON files found in {BRONZE_ELECTRICITY_PATH}"
        )

    for file_path in electricity_files:
        # Example filename:
        # 2026-06-06_NO1.json
        price_area = file_path.stem.split("_")[-1]

        data = read_json(file_path)

        for item in data:
            timestamp_start_raw = item.get("time_start")
            timestamp_end_raw = item.get("time_end")

            timestamp_start_local = pd.to_datetime(timestamp_start_raw)
            timestamp_end_local = pd.to_datetime(timestamp_end_raw)

            rows.append(
                {
                    "timestamp_start_raw": timestamp_start_raw,
                    "timestamp_end_raw": timestamp_end_raw,
                    "timestamp_start_local": timestamp_start_local,
                    "timestamp_end_local": timestamp_end_local,
                    "date": timestamp_start_local.date(),
                    "time": timestamp_start_local.strftime("%H:%M:%S"),
                    "hour": timestamp_start_local.hour,
                    "hour_label": create_hour_label(
                        timestamp_start_local,
                        timestamp_end_local,
                    ),
                    "price_area": price_area,
                    "price_area_name": PRICE_AREA_NAMES.get(price_area),
                    "nok_per_kwh": item.get("NOK_per_kWh"),
                    "eur_per_kwh": item.get("EUR_per_kWh"),
                    "exchange_rate": item.get("EXR"),
                    "source_file": file_path.name,
                    "processed_at": processed_at,
                }
            )

    df = pd.DataFrame(rows)

    output_file = SILVER_PATH / "silver_electricity_prices.csv"
    SILVER_PATH.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_file, index=False)

    print(f"Created {output_file}")
    print(f"Electricity rows: {len(df)}")

    return df


# -----------------------------
# Silver weather table
# -----------------------------

def create_silver_weather_forecast() -> pd.DataFrame:
    """
    Convert raw weather forecast JSON files into a clean Silver table.

    Input:
    data/bronze/weather_forecast/*.json

    Output:
    data/silver/silver_weather_forecast.csv
    """

    rows = []
    processed_at = datetime.now().isoformat(timespec="seconds")

    weather_files = sorted(BRONZE_WEATHER_PATH.glob("*.json"))

    if not weather_files:
        raise FileNotFoundError(
            f"No weather JSON files found in {BRONZE_WEATHER_PATH}"
        )

    for file_path in weather_files:
        # Example filename:
        # 2026-06-06_NO1_Oslo.json
        parts = file_path.stem.split("_")
        price_area = parts[1]
        city = parts[2]

        location = WEATHER_LOCATIONS.get(price_area, {})

        data = read_json(file_path)

        weather_updated_at_utc = safe_get(
            data,
            "properties",
            "meta",
            "updated_at",
        )

        timeseries = safe_get(data, "properties", "timeseries")

        if not timeseries:
            print(f"No timeseries found in {file_path.name}")
            continue

        for item in timeseries:
            forecast_time_raw = item.get("time")

            forecast_time_utc = pd.to_datetime(forecast_time_raw, utc=True)
            forecast_time_local = forecast_time_utc.tz_convert(NORWAY_TIMEZONE)

            instant_details = safe_get(
                item,
                "data",
                "instant",
                "details",
            ) or {}

            next_1h_summary_symbol = safe_get(
                item,
                "data",
                "next_1_hours",
                "summary",
                "symbol_code",
            )

            next_1h_precipitation = safe_get(
                item,
                "data",
                "next_1_hours",
                "details",
                "precipitation_amount",
            )

            next_6h_summary_symbol = safe_get(
                item,
                "data",
                "next_6_hours",
                "summary",
                "symbol_code",
            )

            next_6h_precipitation = safe_get(
                item,
                "data",
                "next_6_hours",
                "details",
                "precipitation_amount",
            )

            next_12h_summary_symbol = safe_get(
                item,
                "data",
                "next_12_hours",
                "summary",
                "symbol_code",
            )

            rows.append(
                {
                    "forecast_time_raw": forecast_time_raw,
                    "forecast_time_utc": forecast_time_utc,
                    "forecast_time_local": forecast_time_local,
                    "date": forecast_time_local.date(),
                    "time": forecast_time_local.strftime("%H:%M:%S"),
                    "hour": forecast_time_local.hour,
                    "price_area": price_area,
                    "city": city,
                    "latitude": location.get("lat"),
                    "longitude": location.get("lon"),
                    "weather_updated_at_utc": weather_updated_at_utc,
                    "air_temperature_celsius": instant_details.get(
                        "air_temperature"
                    ),
                    "wind_speed_mps": instant_details.get("wind_speed"),
                    "wind_from_direction_degrees": instant_details.get(
                        "wind_from_direction"
                    ),
                    "cloud_area_fraction_pct": instant_details.get(
                        "cloud_area_fraction"
                    ),
                    "relative_humidity_pct": instant_details.get(
                        "relative_humidity"
                    ),
                    "air_pressure_hpa": instant_details.get(
                        "air_pressure_at_sea_level"
                    ),
                    "precipitation_next_1h_mm": next_1h_precipitation,
                    "weather_symbol_next_1h": next_1h_summary_symbol,
                    "precipitation_next_6h_mm": next_6h_precipitation,
                    "weather_symbol_next_6h": next_6h_summary_symbol,
                    "weather_symbol_next_12h": next_12h_summary_symbol,
                    "source_file": file_path.name,
                    "processed_at": processed_at,
                }
            )

    df = pd.DataFrame(rows)

    output_file = SILVER_PATH / "silver_weather_forecast.csv"
    SILVER_PATH.mkdir(parents=True, exist_ok=True)

    df.to_csv(output_file, index=False)

    print(f"Created {output_file}")
    print(f"Weather rows: {len(df)}")

    return df


# -----------------------------
# Main function
# -----------------------------

def main() -> None:
    print("Starting Silver transformation...")

    create_silver_electricity_prices()
    create_silver_weather_forecast()

    print("Silver transformation completed.")


if __name__ == "__main__":
    main()