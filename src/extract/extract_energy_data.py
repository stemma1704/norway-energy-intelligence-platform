import json
from datetime import date, datetime
from pathlib import Path

import requests


# -----------------------------
# Project configuration
# -----------------------------

PRICE_AREAS = ["NO1", "NO2", "NO3", "NO4", "NO5"]

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

BRONZE_ELECTRICITY_PATH = Path("data/bronze/electricity_prices")
BRONZE_WEATHER_PATH = Path("data/bronze/weather_forecast")


# -----------------------------
# Helper function
# -----------------------------

def save_json(data, file_path: Path) -> None:
    """
    Save API response data as a JSON file.
    """

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


# -----------------------------
# Electricity price extraction
# -----------------------------

def extract_electricity_prices() -> None:
    """
    Fetch electricity prices for all Norwegian price areas:
    NO1, NO2, NO3, NO4, NO5.

    Source:
    Hva koster strømmen API
    """

    today = date.today()
    year = today.strftime("%Y")
    month_day = today.strftime("%m-%d")

    for price_area in PRICE_AREAS:
        url = (
            "https://www.hvakosterstrommen.no/api/v1/prices/"
            f"{year}/{month_day}_{price_area}.json"
        )

        try:
            response = requests.get(url, timeout=30)

            print(
                f"Electricity API | {price_area} | "
                f"Status: {response.status_code}"
            )

            response.raise_for_status()

            data = response.json()

            output_file = BRONZE_ELECTRICITY_PATH / f"{today}_{price_area}.json"

            save_json(data, output_file)

            print(f"Saved: {output_file}")

        except requests.exceptions.RequestException as error:
            print(f"Failed to fetch electricity data for {price_area}: {error}")


# -----------------------------
# Weather forecast extraction
# -----------------------------

def extract_weather_forecast() -> None:
    """
    Fetch weather forecast data for representative cities
    mapped to Norwegian electricity price areas.

    Source:
    MET Norway Locationforecast API
    """

    url = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

    headers = {
        "User-Agent": "norway-energy-portfolio/1.0 stemy.tomy98@gmail.com"
    }

    today = date.today()

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

            data = response.json()

            output_file = (
                BRONZE_WEATHER_PATH
                / f"{today}_{price_area}_{location['city']}.json"
            )

            save_json(data, output_file)

            print(f"Saved: {output_file}")

        except requests.exceptions.RequestException as error:
            print(
                f"Failed to fetch weather data for "
                f"{price_area} - {location['city']}: {error}"
            )


# -----------------------------
# Main function
# -----------------------------

def main() -> None:
    """
    Run all extraction tasks.
    """

    print("Starting Bronze data extraction...")
    print(f"Run timestamp: {datetime.now().isoformat(timespec='seconds')}")

    extract_electricity_prices()
    extract_weather_forecast()

    print("Bronze data extraction completed.")


if __name__ == "__main__":
    main()