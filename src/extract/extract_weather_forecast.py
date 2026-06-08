import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


# -----------------------------
# Configuration
# -----------------------------

NORWAY_TIMEZONE = ZoneInfo("Europe/Oslo")

BRONZE_WEATHER_PATH = Path("data/bronze/weather_forecast")

WEATHER_LOCATIONS = {
    "NO1": {
        "city": "Oslo",
        "lat": 59.9139,
        "lon": 10.7522,
    },
    "NO2": {
        "city": "Kristiansand",
        "lat": 58.1467,
        "lon": 7.9956,
    },
    "NO3": {
        "city": "Trondheim",
        "lat": 63.4305,
        "lon": 10.3951,
    },
    "NO4": {
        "city": "Tromsø",
        "lat": 69.6492,
        "lon": 18.9553,
    },
    "NO5": {
        "city": "Bergen",
        "lat": 60.3913,
        "lon": 5.3221,
    },
}


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


def convert_utc_to_norway_time(raw_utc_timestamp: str) -> datetime:
    """
    Convert API UTC timestamp into Norway local time.

    Example:
    2026-06-06T13:00:00Z
    becomes
    2026-06-06 15:00:00+02:00 during summer time.
    """
    utc_timestamp = datetime.fromisoformat(
        raw_utc_timestamp.replace("Z", "+00:00")
    )

    return utc_timestamp.astimezone(NORWAY_TIMEZONE)


def create_hour_label(local_timestamp: datetime) -> str:
    """
    Create a readable one-hour label from a forecast timestamp.

    Example:
    15:00 - 16:00
    """
    start_time = local_timestamp.strftime("%H:%M")
    end_time = local_timestamp.replace(hour=(local_timestamp.hour + 1) % 24).strftime(
        "%H:%M"
    )

    return f"{start_time} - {end_time}"


def enrich_weather_timeseries(api_response: dict) -> dict:
    """
    Keep the raw API response, but add readable local time fields
    inside each timeseries item.

    This makes Bronze easier to inspect while preserving the API response.
    """

    timeseries = (
        api_response
        .get("properties", {})
        .get("timeseries", [])
    )

    for item in timeseries:
        forecast_time_raw = item.get("time")

        if not forecast_time_raw:
            continue

        forecast_time_local = convert_utc_to_norway_time(forecast_time_raw)

        item["forecast_time_raw"] = forecast_time_raw
        item["forecast_time_local"] = forecast_time_local.isoformat(timespec="seconds")
        item["local_date"] = forecast_time_local.date().isoformat()
        item["local_time"] = forecast_time_local.strftime("%H:%M:%S")
        item["local_hour"] = forecast_time_local.hour
        item["local_hour_label"] = create_hour_label(forecast_time_local)
    return api_response


def create_empty_daily_weather_file(extraction_date: str) -> dict:
    """
    Create the base structure for one daily weather Bronze file.
    """

    return {
        "extraction_date": extraction_date,
        "source": "met_norway_locationforecast",
        "description": (
            "Daily consolidated weather forecast snapshots. Each snapshot "
            "contains all representative cities and preserves the raw API "
            "response while adding readable local time fields."
        ),
        "snapshots": [],
    }


# -----------------------------
# Main extraction logic
# -----------------------------

def fetch_weather_forecast_snapshot() -> None:
    """
    Fetch weather forecast for all representative locations.

    Output:
    data/bronze/weather_forecast/extraction_date=YYYY-MM-DD.json
    """

    extracted_at = datetime.now(NORWAY_TIMEZONE)
    extraction_date = extracted_at.date().isoformat()

    output_file = BRONZE_WEATHER_PATH / f"extraction_date={extraction_date}.json"

    daily_data = read_json_if_exists(output_file)

    if not daily_data:
        daily_data = create_empty_daily_weather_file(extraction_date)

    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

    headers = {
        "User-Agent": "norway-energy-portfolio/1.0 stemy.tomy98@gmail.com"
    }

    locations = []

    for price_area, location in WEATHER_LOCATIONS.items():
        params = {
            "lat": location["lat"],
            "lon": location["lon"],
        }

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
            )

            print(
                f"Weather API | {price_area} - {location['city']} | "
                f"Status: {response.status_code}"
            )

            response.raise_for_status()

            api_response = response.json()

            enriched_api_response = enrich_weather_timeseries(api_response)

            locations.append(
                {
                    "price_area": price_area,
                    "city": location["city"],
                    "latitude": location["lat"],
                    "longitude": location["lon"],
                    "api_response": enriched_api_response,
                }
            )

        except requests.exceptions.RequestException as error:
            print(
                f"Failed to fetch weather data for "
                f"{price_area} - {location['city']}: {error}"
            )

    snapshot = {
        "extracted_at_raw": extracted_at.isoformat(timespec="seconds"),
        "extracted_date": extracted_at.date().isoformat(),
        "extracted_time": extracted_at.strftime("%H:%M:%S"),
        "extracted_hour": extracted_at.hour,
        "location_count": len(locations),
        "locations": locations,
    }

    daily_data["snapshots"].append(snapshot)

    save_json(daily_data, output_file)

    print(f"Saved consolidated weather file: {output_file}")
    print(f"Locations saved: {len(locations)}")


def main() -> None:
    fetch_weather_forecast_snapshot()


if __name__ == "__main__":
    main()