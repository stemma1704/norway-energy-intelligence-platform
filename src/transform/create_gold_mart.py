from pathlib import Path

import pandas as pd


# -----------------------------
# Configuration
# -----------------------------

SILVER_ELECTRICITY_FILE = Path("data/silver/silver_electricity_prices.csv")
SILVER_WEATHER_FILE = Path("data/silver/silver_weather_forecast.csv")
GOLD_PATH = Path("data/gold")
GOLD_OUTPUT_FILE = GOLD_PATH / "gold_price_weather_mart.csv"


# -----------------------------
# Helper functions
# -----------------------------

def create_price_category(row: pd.Series) -> str:
    """
    Classify each hourly price into a simple business category.

    This compares the hour's price with the daily average price
    for that price area.
    """

    price = row["nok_per_kwh"]
    daily_avg = row["daily_avg_price_nok_per_kwh"]

    if pd.isna(price) or pd.isna(daily_avg):
        return "Unknown"

    if price >= daily_avg * 1.25:
        return "Expensive"
    elif price <= daily_avg * 0.75:
        return "Cheap"
    else:
        return "Normal"


def load_silver_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load Silver electricity and weather tables.
    """

    if not SILVER_ELECTRICITY_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SILVER_ELECTRICITY_FILE}")

    if not SILVER_WEATHER_FILE.exists():
        raise FileNotFoundError(f"Missing file: {SILVER_WEATHER_FILE}")

    electricity = pd.read_csv(SILVER_ELECTRICITY_FILE)
    weather = pd.read_csv(SILVER_WEATHER_FILE)

    return electricity, weather


# -----------------------------
# Gold mart creation
# -----------------------------

def create_gold_price_weather_mart() -> pd.DataFrame:
    """
    Create a Power BI-ready Gold mart by joining electricity prices
    with weather forecast data.

    Join key:
    price_area + date + hour
    """

    electricity, weather = load_silver_tables()

    # -----------------------------
    # Ensure correct datatypes
    # -----------------------------

    electricity["date"] = pd.to_datetime(electricity["date"]).dt.date
    weather["date"] = pd.to_datetime(weather["date"]).dt.date

    electricity["hour"] = electricity["hour"].astype(int)
    weather["hour"] = weather["hour"].astype(int)

    electricity["timestamp_start_local"] = pd.to_datetime(
        electricity["timestamp_start_local"]
    )
    electricity["timestamp_end_local"] = pd.to_datetime(
        electricity["timestamp_end_local"]
    )

    # -----------------------------
    # Keep only useful weather columns for Gold
    # -----------------------------

    weather_selected = weather[
        [
            "price_area",
            "date",
            "hour",
            "city",
            "latitude",
            "longitude",
            "weather_updated_at_utc",
            "air_temperature_celsius",
            "wind_speed_mps",
            "wind_from_direction_degrees",
            "cloud_area_fraction_pct",
            "relative_humidity_pct",
            "air_pressure_hpa",
            "precipitation_next_1h_mm",
            "weather_symbol_next_1h",
            "precipitation_next_6h_mm",
            "weather_symbol_next_6h",
            "weather_symbol_next_12h",
        ]
    ].copy()

    # If multiple weather records exist for the same price_area/date/hour,
    # keep the first one for the MVP.
    weather_selected = weather_selected.drop_duplicates(
        subset=["price_area", "date", "hour"],
        keep="first",
    )

    # -----------------------------
    # Join electricity + weather
    # -----------------------------

    gold = electricity.merge(
        weather_selected,
        on=["price_area", "date", "hour"],
        how="left",
    )

    # -----------------------------
    # Create dashboard-friendly date/time fields
    # -----------------------------

    gold["date_datetime"] = pd.to_datetime(gold["date"])

    gold["date_label"] = gold["date_datetime"].dt.strftime("%-d %B %Y")

    # Windows may not support %-d.
    # If you get an error on Windows, replace the above line with:
    # gold["date_label"] = gold["date_datetime"].dt.strftime("%d %B %Y").str.lstrip("0")

    gold["day_name"] = gold["date_datetime"].dt.day_name()
    gold["month_name"] = gold["date_datetime"].dt.month_name()
    gold["year"] = gold["date_datetime"].dt.year
    gold["month_number"] = gold["date_datetime"].dt.month
    gold["day_of_month"] = gold["date_datetime"].dt.day

    # -----------------------------
    # Daily price metrics
    # -----------------------------

    gold["daily_avg_price_nok_per_kwh"] = gold.groupby(
        ["price_area", "date"]
    )["nok_per_kwh"].transform("mean")

    gold["daily_min_price_nok_per_kwh"] = gold.groupby(
        ["price_area", "date"]
    )["nok_per_kwh"].transform("min")

    gold["daily_max_price_nok_per_kwh"] = gold.groupby(
        ["price_area", "date"]
    )["nok_per_kwh"].transform("max")

    gold["daily_price_spread_nok_per_kwh"] = (
        gold["daily_max_price_nok_per_kwh"]
        - gold["daily_min_price_nok_per_kwh"]
    )

    # -----------------------------
    # Price category flags
    # -----------------------------

    gold["price_category"] = gold.apply(create_price_category, axis=1)

    gold["is_peak_price_hour"] = (
        gold["nok_per_kwh"] == gold["daily_max_price_nok_per_kwh"]
    )

    gold["is_cheap_price_hour"] = (
        gold["nok_per_kwh"] == gold["daily_min_price_nok_per_kwh"]
    )

    # -----------------------------
    # Select final Gold columns
    # -----------------------------

    final_columns = [
        "timestamp_start_local",
        "timestamp_end_local",
        "date",
        "date_label",
        "day_name",
        "month_name",
        "year",
        "month_number",
        "day_of_month",
        "time",
        "hour",
        "hour_label",
        "price_area",
        "price_area_name",
        "city",
        "latitude",
        "longitude",
        "nok_per_kwh",
        "eur_per_kwh",
        "exchange_rate",
        "daily_avg_price_nok_per_kwh",
        "daily_min_price_nok_per_kwh",
        "daily_max_price_nok_per_kwh",
        "daily_price_spread_nok_per_kwh",
        "price_category",
        "is_peak_price_hour",
        "is_cheap_price_hour",
        "air_temperature_celsius",
        "wind_speed_mps",
        "wind_from_direction_degrees",
        "cloud_area_fraction_pct",
        "relative_humidity_pct",
        "air_pressure_hpa",
        "precipitation_next_1h_mm",
        "weather_symbol_next_1h",
        "precipitation_next_6h_mm",
        "weather_symbol_next_6h",
        "weather_symbol_next_12h",
        "weather_updated_at_utc",
        "source_file",
        "processed_at",
    ]

    gold = gold[final_columns]

    # -----------------------------
    # Save Gold output
    # -----------------------------

    GOLD_PATH.mkdir(parents=True, exist_ok=True)

    gold.to_csv(GOLD_OUTPUT_FILE, index=False)

    print(f"Created {GOLD_OUTPUT_FILE}")
    print(f"Gold rows: {len(gold)}")
    print(f"Gold columns: {len(gold.columns)}")

    return gold


# -----------------------------
# Main
# -----------------------------

if __name__ == "__main__":
    create_gold_price_weather_mart()