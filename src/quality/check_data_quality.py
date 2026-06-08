from pathlib import Path

import pandas as pd


# -----------------------------
# File paths
# -----------------------------

SILVER_ELECTRICITY_FILE = Path("data/silver/silver_electricity_prices.csv")
SILVER_WEATHER_FILE = Path("data/silver/silver_weather_forecast.csv")
GOLD_FILE = Path("data/gold/gold_price_weather_mart.csv")


# -----------------------------
# Generic checks
# -----------------------------

def check_file_exists(file_path: Path) -> None:
    """
    Check whether a required file exists.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Missing required file: {file_path}")

    print(f"✅ File exists: {file_path}")


def check_no_empty_dataframe(df: pd.DataFrame, name: str) -> None:
    """
    Check whether a dataframe has at least one row.
    """
    if df.empty:
        raise ValueError(f"{name} is empty")

    print(f"✅ {name} is not empty: {len(df)} rows")


def check_required_columns(
    df: pd.DataFrame,
    name: str,
    required_columns: list[str],
) -> None:
    """
    Check whether all required columns are present.
    """
    missing_columns = [column for column in required_columns if column not in df.columns]

    if missing_columns:
        raise ValueError(f"{name} is missing required columns: {missing_columns}")

    print(f"✅ {name} has all required columns")


def check_no_nulls_in_required_columns(
    df: pd.DataFrame,
    name: str,
    required_non_null_columns: list[str],
) -> None:
    """
    Check that critical columns do not contain null values.

    Important:
    This check does not fill missing values.
    It fails if critical values are missing.
    """
    null_counts = df[required_non_null_columns].isna().sum()
    failing_columns = null_counts[null_counts > 0]

    if not failing_columns.empty:
        raise ValueError(
            f"{name} has null values in required columns:\n{failing_columns}"
        )

    print(f"✅ {name} has no nulls in required columns")


def check_allowed_price_areas(df: pd.DataFrame, name: str) -> None:
    """
    Check that price_area only contains expected Norwegian price areas.
    """
    allowed_price_areas = {"NO1", "NO2", "NO3", "NO4", "NO5"}
    actual_price_areas = set(df["price_area"].dropna().unique())

    unexpected_price_areas = actual_price_areas - allowed_price_areas

    if unexpected_price_areas:
        raise ValueError(
            f"{name} has unexpected price areas: {unexpected_price_areas}"
        )

    print(f"✅ {name} price areas are valid: {sorted(actual_price_areas)}")


def check_hour_range(df: pd.DataFrame, name: str) -> None:
    """
    Check that hour values are between 0 and 23.
    """
    invalid_hours = df[~df["hour"].between(0, 23)]

    if not invalid_hours.empty:
        raise ValueError(
            f"{name} has invalid hour values outside 0–23:\n"
            f"{invalid_hours[['date', 'price_area', 'hour']].head(10)}"
        )

    print(f"✅ {name} hour values are valid: 0–23")


def check_no_duplicate_keys(
    df: pd.DataFrame,
    name: str,
    key_columns: list[str],
) -> None:
    """
    Check that a table does not contain duplicate business keys.

    Example key:
    price_area + date + hour

    This is important because duplicate keys can cause duplicated rows
    after joins and misleading Power BI results.
    """
    duplicate_rows = df[df.duplicated(subset=key_columns, keep=False)]

    if not duplicate_rows.empty:
        raise ValueError(
            f"{name} has duplicate keys based on {key_columns}.\n"
            f"Sample duplicate rows:\n{duplicate_rows[key_columns].head(10)}"
        )

    print(f"✅ {name} has no duplicate keys for {key_columns}")


def check_numeric_column_range(
    df: pd.DataFrame,
    name: str,
    column: str,
    min_value: float | None = None,
    max_value: float | None = None,
) -> None:
    """
    Check that numeric values are within a reasonable range.

    This is not meant to be perfect. It catches clearly wrong values.
    """
    if column not in df.columns:
        raise ValueError(f"{name} does not contain column: {column}")

    series = pd.to_numeric(df[column], errors="coerce")

    if min_value is not None:
        invalid_min = df[series < min_value]

        if not invalid_min.empty:
            raise ValueError(
                f"{name}.{column} has values below {min_value}.\n"
                f"Sample:\n{invalid_min[[column]].head(10)}"
            )

    if max_value is not None:
        invalid_max = df[series > max_value]

        if not invalid_max.empty:
            raise ValueError(
                f"{name}.{column} has values above {max_value}.\n"
                f"Sample:\n{invalid_max[[column]].head(10)}"
            )

    print(f"✅ {name}.{column} values are within expected range")


# -----------------------------
# Electricity-specific checks
# -----------------------------

def check_electricity_row_counts(electricity: pd.DataFrame) -> None:
    """
    Check that each date and price area has about 24 hourly rows.

    Electricity price data should normally have 24 rows per price area per day.
    Some days can have 23 or 25 hours because of daylight saving time changes,
    but 24 is expected for normal days.
    """
    row_counts = electricity.groupby(["date", "price_area"]).size()

    unusual_counts = row_counts[~row_counts.isin([23, 24, 25])]

    if not unusual_counts.empty:
        raise ValueError(
            "Electricity has unusual row counts for some date/price_area groups.\n"
            f"Expected 23, 24, or 25 rows depending on daylight saving time.\n"
            f"Found:\n{unusual_counts}"
        )

    print("✅ Electricity row counts look valid: 23, 24, or 25 rows per date/price_area")


def check_electricity_prices(electricity: pd.DataFrame) -> None:
    """
    Check that electricity prices are not negative.

    Negative prices can happen in some power markets, but for this MVP,
    we flag them as a warning instead of failing.
    """
    negative_prices = electricity[electricity["nok_per_kwh"] < 0]

    if not negative_prices.empty:
        print(
            "⚠️ Warning: Negative electricity prices found. "
            "This can happen in real electricity markets, but review the rows:"
        )
        print(negative_prices[["date", "hour", "price_area", "nok_per_kwh"]].head(10))
    else:
        print("✅ Electricity prices are not negative")


# -----------------------------
# Weather-specific checks
# -----------------------------

def check_weather_temperature_range(weather: pd.DataFrame) -> None:
    """
    Check that temperature values are within a broad realistic range for Norway.
    """
    check_numeric_column_range(
        weather,
        "Silver weather",
        "air_temperature_celsius",
        min_value=-60,
        max_value=45,
    )


def check_weather_wind_speed_range(weather: pd.DataFrame) -> None:
    """
    Check that wind speed is not negative and not unreasonably high.
    """
    check_numeric_column_range(
        weather,
        "Silver weather",
        "wind_speed_mps",
        min_value=0,
        max_value=80,
    )


def check_weather_precipitation_range(weather: pd.DataFrame) -> None:
    """
    Check that precipitation fields are not negative.

    Missing precipitation can be allowed because the weather API does not always
    return every next_1h, next_6h, or next_12h section.
    """
    precipitation_columns = [
        "precipitation_next_1h_mm",
        "precipitation_next_6h_mm",
    ]

    for column in precipitation_columns:
        if column in weather.columns:
            series = pd.to_numeric(weather[column], errors="coerce")
            negative_values = weather[series < 0]

            if not negative_values.empty:
                raise ValueError(
                    f"Silver weather.{column} contains negative precipitation values.\n"
                    f"Sample:\n{negative_values[[column]].head(10)}"
                )

            print(f"✅ Silver weather.{column} has no negative values")


# -----------------------------
# Gold-specific checks
# -----------------------------

def check_gold_row_count_matches_electricity(
    electricity: pd.DataFrame,
    gold: pd.DataFrame,
) -> None:
    """
    Gold is built using electricity as the left/main table.

    Therefore, Gold should normally have the same number of rows as Silver electricity.
    """
    electricity_rows = len(electricity)
    gold_rows = len(gold)

    if electricity_rows != gold_rows:
        raise ValueError(
            f"Gold row count does not match Silver electricity.\n"
            f"Silver electricity rows: {electricity_rows}\n"
            f"Gold rows: {gold_rows}"
        )

    print("✅ Gold row count matches Silver electricity row count")


def check_gold_weather_join_completeness(gold: pd.DataFrame) -> None:
    """
    Check how many Gold rows are missing weather data after the join.

    Some missing weather rows may happen because weather forecast data starts
    from the API response time and may not cover all electricity hours for today.

    This check prints the percentage and only fails if more than 50% is missing.
    """
    total_rows = len(gold)

    if total_rows == 0:
        raise ValueError("Gold mart is empty")

    missing_weather_count = gold["air_temperature_celsius"].isna().sum()
    missing_percentage = (missing_weather_count / total_rows) * 100

    print(
        f"Gold rows missing weather temperature: "
        f"{missing_weather_count}/{total_rows} ({missing_percentage:.2f}%)"
    )

    if missing_percentage > 50:
        raise ValueError(
            "More than 50% of Gold rows are missing weather data. "
            "Check timezone conversion, weather forecast coverage, and join keys."
        )

    print("✅ Gold weather join completeness is acceptable")


def check_price_category_values(gold: pd.DataFrame) -> None:
    """
    Check that price_category only contains expected values.
    """
    allowed_categories = {"Cheap", "Normal", "Expensive", "Unknown"}
    actual_categories = set(gold["price_category"].dropna().unique())

    unexpected_categories = actual_categories - allowed_categories

    if unexpected_categories:
        raise ValueError(
            f"Gold mart has unexpected price_category values: {unexpected_categories}"
        )

    print(f"✅ Gold price_category values are valid: {sorted(actual_categories)}")


# -----------------------------
# Main quality runner
# -----------------------------

def run_quality_checks() -> None:
    """
    Run all data quality checks.

    This script validates data.
    It does not remove duplicates.
    It does not fill missing values.
    It does not overwrite any data files.
    """

    print("\nStarting data quality checks...")
    print("--------------------------------")

    # File existence checks
    check_file_exists(SILVER_ELECTRICITY_FILE)
    check_file_exists(SILVER_WEATHER_FILE)
    check_file_exists(GOLD_FILE)

    # Load files
    electricity = pd.read_csv(SILVER_ELECTRICITY_FILE)
    weather = pd.read_csv(SILVER_WEATHER_FILE)
    gold = pd.read_csv(GOLD_FILE)

    # Basic dataframe checks
    check_no_empty_dataframe(electricity, "Silver electricity")
    check_no_empty_dataframe(weather, "Silver weather")
    check_no_empty_dataframe(gold, "Gold mart")

    # Required column checks
    check_required_columns(
        electricity,
        "Silver electricity",
        [
            "timestamp_start_local",
            "timestamp_end_local",
            "date",
            "time",
            "hour",
            "hour_label",
            "price_area",
            "price_area_name",
            "nok_per_kwh",
            "eur_per_kwh",
            "exchange_rate",
            "source_file",
            "processed_at",
        ],
    )

    check_required_columns(
        weather,
        "Silver weather",
        [
            "forecast_time_utc",
            "forecast_time_local",
            "date",
            "time",
            "hour",
            "price_area",
            "city",
            "latitude",
            "longitude",
            "weather_updated_at_utc",
            "air_temperature_celsius",
            "wind_speed_mps",
            "cloud_area_fraction_pct",
            "precipitation_next_1h_mm",
            "weather_symbol_next_1h",
            "source_file",
            "processed_at",
        ],
    )

    check_required_columns(
        gold,
        "Gold mart",
        [
            "date",
            "date_label",
            "day_name",
            "time",
            "hour",
            "hour_label",
            "price_area",
            "price_area_name",
            "nok_per_kwh",
            "daily_avg_price_nok_per_kwh",
            "price_category",
            "is_peak_price_hour",
            "is_cheap_price_hour",
            "air_temperature_celsius",
        ],
    )

    # Critical non-null checks
    check_no_nulls_in_required_columns(
        electricity,
        "Silver electricity",
        [
            "date",
            "hour",
            "price_area",
            "price_area_name",
            "nok_per_kwh",
            "timestamp_start_local",
            "timestamp_end_local",
        ],
    )

    check_no_nulls_in_required_columns(
        weather,
        "Silver weather",
        [
            "date",
            "hour",
            "price_area",
            "city",
            "forecast_time_utc",
            "forecast_time_local",
            "air_temperature_celsius",
        ],
    )

    check_no_nulls_in_required_columns(
        gold,
        "Gold mart",
        [
            "date",
            "hour",
            "price_area",
            "price_area_name",
            "nok_per_kwh",
            "price_category",
        ],
    )

    # Domain checks
    check_allowed_price_areas(electricity, "Silver electricity")
    check_allowed_price_areas(weather, "Silver weather")
    check_allowed_price_areas(gold, "Gold mart")

    check_hour_range(electricity, "Silver electricity")
    check_hour_range(weather, "Silver weather")
    check_hour_range(gold, "Gold mart")

    # Duplicate business key checks
    check_no_duplicate_keys(
        electricity,
        "Silver electricity",
        ["price_area", "date", "hour"],
    )

    check_no_duplicate_keys(
        gold,
        "Gold mart",
        ["price_area", "date", "hour"],
    )

    # Electricity checks
    check_electricity_row_counts(electricity)
    check_electricity_prices(electricity)

    # Weather checks
    check_weather_temperature_range(weather)
    check_weather_wind_speed_range(weather)
    check_weather_precipitation_range(weather)

    # Gold checks
    check_gold_row_count_matches_electricity(electricity, gold)
    check_gold_weather_join_completeness(gold)
    check_price_category_values(gold)

    print("--------------------------------")
    print("All data quality checks completed successfully.")


if __name__ == "__main__":
    run_quality_checks()