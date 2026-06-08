import json
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


# -----------------------------
# Configuration
# -----------------------------

NORWAY_TIMEZONE = ZoneInfo("Europe/Oslo")

PRICE_AREAS = ["NO1", "NO2", "NO3", "NO4", "NO5"]

PRICE_AREA_NAMES = {
    "NO1": "Eastern Norway / Oslo",
    "NO2": "Southern Norway / Kristiansand",
    "NO3": "Central Norway / Trondheim",
    "NO4": "Northern Norway / Tromsø",
    "NO5": "Western Norway / Bergen",
}

BRONZE_ELECTRICITY_PATH = Path("data/bronze/electricity_prices")


# -----------------------------
# Helper functions
# -----------------------------

def read_json_if_exists(file_path: Path) -> dict:
    """
    Read an existing JSON file.

    If the file does not exist, return an empty dictionary.
    """
    if not file_path.exists():
        return {}

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(data: dict, file_path: Path) -> None:
    """
    Save data to a JSON file.
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def create_hour_label(start_timestamp: datetime, end_timestamp: datetime) -> str:
    """
    Create a readable hour label.

    Example:
    00:00 - 01:00
    """
    return f"{start_timestamp.strftime('%H:%M')} - {end_timestamp.strftime('%H:%M')}"


def enrich_electricity_record(
    raw_record: dict,
    price_area: str,
) -> dict:
    """
    Keep raw API values and add user-friendly time fields.

    We do not remove the original timestamp values.
    We add extra fields to make the Bronze JSON easier to inspect.
    """

    time_start_raw = raw_record.get("time_start")
    time_end_raw = raw_record.get("time_end")

    start_timestamp = datetime.fromisoformat(time_start_raw)
    end_timestamp = datetime.fromisoformat(time_end_raw)

    return {
        "price_area": price_area,
        "price_area_name": PRICE_AREA_NAMES.get(price_area),

        # Raw API timestamps preserved
        "time_start_raw": time_start_raw,
        "time_end_raw": time_end_raw,

        # User-friendly time fields
        "date": start_timestamp.date().isoformat(),
        "start_time": start_timestamp.strftime("%H:%M:%S"),
        "end_time": end_timestamp.strftime("%H:%M:%S"),
        "hour": start_timestamp.hour,
        "hour_label": create_hour_label(start_timestamp, end_timestamp),

        # Raw API price values preserved
        "NOK_per_kWh": raw_record.get("NOK_per_kWh"),
        "EUR_per_kWh": raw_record.get("EUR_per_kWh"),
        "EXR": raw_record.get("EXR"),
    }


def create_empty_daily_electricity_file(price_date: date) -> dict:
    """
    Create the base structure for one daily electricity Bronze file.
    """

    return {
        "price_date": price_date.isoformat(),
        "source": "hvakosterstrommen",
        "description": (
            "Consolidated raw electricity price API data for all Norwegian "
            "price areas. Raw API timestamp values are preserved and readable "
            "date/time helper fields are added."
        ),
        "extraction_runs": [],
    }


# -----------------------------
# Main extraction logic
# -----------------------------

def fetch_electricity_prices_for_date(price_date: date) -> None:
    """
    Fetch electricity prices for all price areas for one price date.

    Output:
    data/bronze/electricity_prices/price_date=YYYY-MM-DD.json
    """

    extracted_at = datetime.now(NORWAY_TIMEZONE)

    output_file = BRONZE_ELECTRICITY_PATH / f"price_date={price_date}.json"

    daily_data = read_json_if_exists(output_file)

    if not daily_data:
        daily_data = create_empty_daily_electricity_file(price_date)

    records = []

    year = price_date.strftime("%Y")
    month_day = price_date.strftime("%m-%d")

    for price_area in PRICE_AREAS:
        url = (
            "https://www.hvakosterstrommen.no/api/v1/prices/"
            f"{year}/{month_day}_{price_area}.json"
        )

        try:
            response = requests.get(url, timeout=30)

            print(
                f"Electricity API | price_date={price_date} | "
                f"{price_area} | Status: {response.status_code}"
            )

            response.raise_for_status()

            raw_records = response.json()

            for raw_record in raw_records:
                enriched_record = enrich_electricity_record(
                    raw_record=raw_record,
                    price_area=price_area,
                )
                records.append(enriched_record)

        except requests.exceptions.RequestException as error:
            print(
                f"Failed to fetch electricity data for "
                f"{price_area} on {price_date}: {error}"
            )

    extraction_run = {
        "extracted_at_raw": extracted_at.isoformat(timespec="seconds"),
        "extracted_date": extracted_at.date().isoformat(),
        "extracted_time": extracted_at.strftime("%H:%M:%S"),
        "price_date": price_date.isoformat(),
        "record_count": len(records),
        "records": records,
    }

    daily_data["extraction_runs"].append(extraction_run)

    save_json(daily_data, output_file)

    print(f"Saved consolidated electricity file: {output_file}")
    print(f"Records saved: {len(records)}")


def main() -> None:
    """
    Fetch electricity prices for today and tomorrow.

    Tomorrow's prices may fail if they are not published yet.
    That is okay.
    """

    today = date.today()
    tomorrow = today + timedelta(days=1)

    fetch_electricity_prices_for_date(today)
    fetch_electricity_prices_for_date(tomorrow)


if __name__ == "__main__":
    main()