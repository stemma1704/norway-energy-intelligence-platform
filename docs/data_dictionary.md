# Data Dictionary — Norway Energy Intelligence Platform ⚡🌦️

## 1. What is this document about?

This document explains the raw data used in the **Norway Energy Intelligence Platform**.

The project combines two API data sources:

1. **Electricity price data** ⚡
   Hourly electricity prices for Norwegian price areas such as NO1, NO2, NO3, NO4, and NO5.

2. **Weather forecast data** 🌦️
   Forecasted weather values for representative cities such as Oslo, Kristiansand, Trondheim, Tromsø, and Bergen.

The purpose of this document is to clearly describe:

* What fields are available in the raw Bronze JSON files
* What each field means
* Whether the field should be used in the Silver transformation layer
* Why some fields are selected and others are ignored
* How raw API timestamps are preserved while readable date/time fields are added

The Silver layer will transform raw JSON into clean tabular datasets that can later be joined in the Gold layer and used in Power BI.

---

## 2. Quick view

| Source            | Bronze File Type                 | Data Grain                              | Main Use                           |
| ----------------- | -------------------------------- | --------------------------------------- | ---------------------------------- |
| Electricity API ⚡ | Consolidated daily JSON          | One row per price area per hour         | Hourly electricity price analysis  |
| Weather API 🌦️   | Consolidated daily snapshot JSON | One row per city per forecast timestamp | Weather context for price analysis |

---

## 3. Data flow

```text
⚡ Electricity API        🌦️ Weather API
        ↓                     ↓
        🥉 Bronze Layer: consolidated raw JSON files
                  ↓
        🥈 Silver Layer: cleaned tables
                  ↓
        🥇 Gold Layer: joined analytics mart
                  ↓
        📊 Power BI dashboard
```

---

## 4. Field priority legend

| Symbol              | Meaning                                                 |
| ------------------- | ------------------------------------------------------- |
| ✅ Core field        | Required for the MVP dashboard                          |
| 🟡 Supporting field | Useful, but not essential for the first dashboard       |
| 🔵 Metadata field   | Useful for tracking, lineage, debugging, or monitoring  |
| ❌ Ignored for MVP   | Available in raw data but not used in the first version |

---

# Electricity Data ⚡

## 5. Electricity data file

### File description

The electricity Bronze file is stored as **one consolidated JSON file per price date**.

Example Bronze file:

```text
data/bronze/electricity_prices/price_date=2026-06-06.json
```

This file contains:

* All five Norwegian price areas: NO1, NO2, NO3, NO4, NO5
* Around 24 hourly records per price area
* Around 120 electricity price records per price date
* One or more extraction runs
* Raw API timestamps preserved
* Additional readable date/time helper fields added by our extraction script

This structure is cleaner than storing one JSON file per price area because one daily file now contains all electricity price data for that date.

---

## 6. Electricity Bronze JSON structure

Example structure:

```json
{
  "price_date": "2026-06-06",
  "source": "hvakosterstrommen",
  "description": "Consolidated raw electricity price API data for all Norwegian price areas. Raw API timestamp values are preserved and readable date/time helper fields are added.",
  "extraction_runs": [
    {
      "extracted_at_raw": "2026-06-06T14:05:22+02:00",
      "extracted_date": "2026-06-06",
      "extracted_time": "14:05:22",
      "price_date": "2026-06-06",
      "record_count": 120,
      "records": [
        {
          "price_area": "NO1",
          "price_area_name": "Eastern Norway / Oslo",
          "time_start_raw": "2026-06-06T00:00:00+02:00",
          "time_end_raw": "2026-06-06T01:00:00+02:00",
          "date": "2026-06-06",
          "start_time": "00:00:00",
          "end_time": "01:00:00",
          "hour": 0,
          "hour_label": "00:00 - 01:00",
          "NOK_per_kWh": 1.19029,
          "EUR_per_kWh": 0.10976,
          "EXR": 10.8445
        }
      ]
    }
  ]
}
```

---

## 7. Electricity data fields

| Raw Field / Section | Meaning                                                                                                                                                               | Use in Silver Layer?                                                                                                   |
| ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `price_date`        | The date the electricity prices belong to. Example: `2026-06-06`. This is the business date of the electricity price, not necessarily the date we collected the data. | ✅ **Yes — core field.** Becomes `price_date`. Useful for filtering, validation, and historical backfill.               |
| `source`            | Name of the data source. Example: `hvakosterstrommen`.                                                                                                                | 🔵 **Yes — metadata field.** Useful for data lineage and documentation.                                                |
| `description`       | Human-readable explanation of what the Bronze file contains.                                                                                                          | ❌ **No — ignored for analytics.** Useful in raw JSON but not needed in Silver tables.                                  |
| `extraction_runs`   | List of API extraction attempts/runs stored inside the daily file. If the same day is collected more than once, multiple runs can exist.                              | ✅ **Yes — core structure.** Silver reads records from this list.                                                       |
| `extracted_at_raw`  | Exact timestamp when our pipeline collected the data. Example: `2026-06-06T14:05:22+02:00`.                                                                           | 🔵 **Yes — metadata field.** Becomes `extracted_at_raw`. Useful for lineage and debugging.                             |
| `extracted_date`    | Date when the pipeline collected the data. Example: `2026-06-06`.                                                                                                     | 🔵 **Yes — metadata field.** Useful for tracking when data was pulled.                                                 |
| `extracted_time`    | Time when the pipeline collected the data. Example: `14:05:22`.                                                                                                       | 🔵 **Yes — metadata field.** Useful for checking whether the morning or afternoon extraction produced the data.        |
| `record_count`      | Number of records collected in that extraction run. For a normal full day: `5 price areas × 24 hours = 120 records`.                                                  | 🔵 **Optional metadata field.** Useful for validation.                                                                 |
| `records`           | List of hourly electricity price records for all price areas.                                                                                                         | ✅ **Yes — core structure.** Silver loops through this list to create rows.                                             |
| `price_area`        | Norwegian electricity price area code. Examples: `NO1`, `NO2`, `NO3`, `NO4`, `NO5`.                                                                                   | ✅ **Yes — core field.** Becomes `price_area`. Required for comparing regions and joining with weather.                 |
| `price_area_name`   | Human-readable name for the price area. Example: `NO1` = `Eastern Norway / Oslo`.                                                                                     | ✅ **Yes — core field.** Becomes `price_area_name`. Makes Power BI visuals easier to understand.                        |
| `time_start_raw`    | Original API start timestamp for the hourly price interval. Example: `2026-06-06T00:00:00+02:00`. This preserves timezone information.                                | ✅ **Yes — core field.** Becomes `timestamp_start_raw` and `timestamp_start_local`. Used for time analysis.             |
| `time_end_raw`      | Original API end timestamp for the hourly price interval. Example: `2026-06-06T01:00:00+02:00`.                                                                       | ✅ **Yes — core field.** Becomes `timestamp_end_raw` and `timestamp_end_local`. Used to define the hourly price window. |
| `date`              | Readable local date derived from `time_start_raw`. Example: `2026-06-06`.                                                                                             | ✅ **Yes — core field.** Becomes `date`. Used for filtering, grouping, and joining with weather.                        |
| `start_time`        | Readable local start time derived from `time_start_raw`. Example: `00:00:00`.                                                                                         | ✅ **Yes — core field.** Becomes `time`. Used for display and hourly analysis.                                          |
| `end_time`          | Readable local end time derived from `time_end_raw`. Example: `01:00:00`.                                                                                             | 🟡 **Yes — supporting field.** Used to create or validate `hour_label`.                                                |
| `hour`              | Numeric hour extracted from the local start time. Example: `0` for midnight, `15` for 15:00.                                                                          | ✅ **Yes — core field.** Becomes `hour`. Required for hourly joins and sorting.                                         |
| `hour_label`        | User-friendly hourly interval. Example: `00:00 - 01:00`.                                                                                                              | ✅ **Yes — core field.** Becomes `hour_label`. Useful for Power BI axis labels and tooltips.                            |
| `NOK_per_kWh`       | Electricity price in Norwegian kroner per kilowatt-hour. Example: `1.19029` means 1 kWh costs about 1.19029 NOK during that hour.                                     | ✅ **Yes — core field.** Becomes `nok_per_kwh`. Main KPI for the dashboard.                                             |
| `EUR_per_kWh`       | Electricity price in euros per kilowatt-hour. Useful because Nordic and European electricity markets often use euro-based pricing.                                    | 🟡 **Yes — supporting field.** Becomes `eur_per_kwh`. Useful for future European market comparison.                    |
| `EXR`               | Exchange rate used between EUR and NOK. Example: `10.8445` means 1 EUR is approximately 10.8445 NOK.                                                                  | 🟡 **Yes — supporting field.** Becomes `exchange_rate`. Helps explain the relationship between EUR and NOK prices.     |
| `source_file`       | Name of the Bronze JSON file that produced the row. Example: `price_date=2026-06-06.json`.                                                                            | 🔵 **Yes — metadata field.** Created in Silver as `source_file`. Useful for debugging and data lineage.                |
| `processed_at`      | Time when our Python transformation processed the row. This is created during Silver transformation, not by the API.                                                  | 🔵 **Yes — metadata field.** Becomes `processed_at`. Helps track when Silver was created.                              |

---

## 8. Why these electricity fields matter

The electricity table gives us three essential things:

| Concept                | Field Examples                                                 | Why it matters                                      |
| ---------------------- | -------------------------------------------------------------- | --------------------------------------------------- |
| Price                  | `NOK_per_kWh`, `EUR_per_kWh`                                   | Shows how expensive electricity is during each hour |
| Time                   | `time_start_raw`, `time_end_raw`, `date`, `hour`, `hour_label` | Shows when each price is valid                      |
| Location / market area | `price_area`, `price_area_name`                                | Allows comparison across Norwegian price areas      |
| Lineage                | `extracted_at_raw`, `source_file`, `processed_at`              | Helps track when data was collected and transformed |

Together, these fields allow us to answer:

* Which hour is cheapest?
* Which hour is most expensive?
* Which price area has the highest price?
* How do prices change during the day?
* When was the data collected?
* Which raw file produced this row?

---

# Weather Data 🌦️

## 9. Weather data file

### File description

The weather Bronze file is stored as **one consolidated JSON file per extraction date**.

Example Bronze file:

```text
data/bronze/weather_forecast/extraction_date=2026-06-06.json
```

This file contains:

* One extraction date
* One or more weather forecast snapshots for that date
* All representative cities in each snapshot
* The original MET Norway API response for each city
* Raw UTC forecast timestamps preserved
* Additional Norway local date/time fields added by our extraction script

Weather forecasts are snapshots. If the API is called multiple times in a day, each run is appended to the same daily weather file under `snapshots`.

---

## 10. Weather city mapping

In this project, each electricity price area is represented by one city.

| Price Area | Representative City |
| ---------- | ------------------- |
| NO1        | Oslo                |
| NO2        | Kristiansand        |
| NO3        | Trondheim           |
| NO4        | Tromsø              |
| NO5        | Bergen              |

---

## 11. Weather Bronze JSON structure

Example structure:

```json
{
  "extraction_date": "2026-06-06",
  "source": "met_norway_locationforecast",
  "description": "Daily consolidated weather forecast snapshots. Each snapshot contains all representative cities and preserves the raw API response while adding readable local time fields.",
  "snapshots": [
    {
      "extracted_at_raw": "2026-06-06T15:00:00+02:00",
      "extracted_date": "2026-06-06",
      "extracted_time": "15:00:00",
      "extracted_hour": 15,
      "location_count": 5,
      "locations": [
        {
          "price_area": "NO1",
          "city": "Oslo",
          "latitude": 59.9139,
          "longitude": 10.7522,
          "api_response": {
            "type": "Feature",
            "geometry": {
              "type": "Point",
              "coordinates": [10.7522, 59.9139, 5]
            },
            "properties": {
              "meta": {
                "updated_at": "2026-06-06T13:27:40Z"
              },
              "timeseries": [
                {
                  "time": "2026-06-06T13:00:00Z",
                  "forecast_time_raw": "2026-06-06T13:00:00Z",
                  "forecast_time_local": "2026-06-06T15:00:00+02:00",
                  "local_date": "2026-06-06",
                  "local_time": "15:00:00",
                  "local_hour": 15,
                  "local_hour_label": "15:00 - 16:00",
                  "data": {
                    "instant": {
                      "details": {
                        "air_temperature": 21.0,
                        "wind_speed": 3.8,
                        "cloud_area_fraction": 53.5
                      }
                    }
                  }
                }
              ]
            }
          }
        }
      ]
    }
  ]
}
```

---

## 12. Weather data fields

| Raw Field / Section                              | Meaning                                                                                                             | Use in Silver Layer?                                                                                                        |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `extraction_date`                                | Date when the daily weather Bronze file was created. Example: `2026-06-06`.                                         | 🔵 **Yes — metadata field.** Useful for tracking the daily weather snapshot file.                                           |
| `source`                                         | Name of the weather data source. Example: `met_norway_locationforecast`.                                            | 🔵 **Yes — metadata field.** Useful for data lineage.                                                                       |
| `description`                                    | Human-readable explanation of what the Bronze file contains.                                                        | ❌ **No — ignored for analytics.** Useful in raw JSON but not needed in Silver.                                              |
| `snapshots`                                      | List of weather API extraction runs for the day. Each snapshot represents one API call time.                        | ✅ **Yes — core structure.** Silver reads from this list.                                                                    |
| `extracted_at_raw`                               | Exact timestamp when the weather API snapshot was collected. Example: `2026-06-06T15:00:00+02:00`.                  | 🔵 **Yes — metadata field.** Becomes `extracted_at_raw`. Useful for tracking forecast snapshots.                            |
| `extracted_date`                                 | Date when the weather snapshot was collected.                                                                       | 🔵 **Yes — metadata field.** Useful for lineage and monitoring.                                                             |
| `extracted_time`                                 | Time when the weather snapshot was collected. Example: `15:00:00`.                                                  | 🔵 **Yes — metadata field.** Useful for knowing which API call produced the forecast.                                       |
| `extracted_hour`                                 | Hour when the snapshot was collected. Example: `15`.                                                                | 🔵 **Yes — metadata field.** Useful for snapshot-level analysis.                                                            |
| `location_count`                                 | Number of city/location API responses collected in the snapshot. Expected value is usually `5`.                     | 🔵 **Optional metadata field.** Useful for validation.                                                                      |
| `locations`                                      | List of representative cities collected in the snapshot.                                                            | ✅ **Yes — core structure.** Silver loops through this list.                                                                 |
| `price_area`                                     | Norwegian electricity price area connected to the weather city. Example: `NO1`.                                     | ✅ **Yes — core field.** Becomes `price_area`. Required for joining with electricity prices.                                 |
| `city`                                           | Representative city for the weather forecast. Example: `Oslo`.                                                      | ✅ **Yes — core field.** Becomes `city`. Useful for dashboard labels.                                                        |
| `latitude`                                       | Latitude of the representative city.                                                                                | 🟡 **Yes — supporting field.** Becomes `latitude`. Useful for map visuals.                                                  |
| `longitude`                                      | Longitude of the representative city.                                                                               | 🟡 **Yes — supporting field.** Becomes `longitude`. Useful for map visuals.                                                 |
| `api_response`                                   | Original MET Norway API response for the location.                                                                  | ✅ **Yes — core structure.** Silver extracts forecast records from this object.                                              |
| `type`                                           | Describes the type of object returned by the API. Example: `Feature`.                                               | ❌ **No — ignored for MVP.** API/geospatial metadata not needed for the first dashboard.                                     |
| `geometry.coordinates`                           | Location coordinates from the API response. Order is longitude, latitude, altitude.                                 | 🟡 **Partially yes.** We already store latitude and longitude at location level. Altitude is ignored for MVP.               |
| `properties.meta.updated_at`                     | Timestamp showing when the weather forecast was last updated by the provider. Example: `2026-06-06T13:27:40Z`.      | 🔵 **Yes — metadata field.** Becomes `weather_updated_at_utc`. Useful for data freshness.                                   |
| `properties.meta.units`                          | Measurement units for weather fields, such as Celsius, m/s, percent, and millimetres.                               | ❌ **No as a separate field.** Units are added into Silver column names, such as `air_temperature_celsius`.                  |
| `properties.timeseries`                          | List of forecast records. Each item represents one forecast timestamp.                                              | ✅ **Yes — core structure.** Silver creates one row per forecast timestamp.                                                  |
| `properties.timeseries[].time`                   | Original MET Norway UTC forecast timestamp. Example: `2026-06-06T13:00:00Z`. This raw API field is not overwritten. | ✅ **Yes — core field.** Becomes `forecast_time_utc` and is also preserved as raw time reference.                            |
| `forecast_time_raw`                              | Copy of the original UTC forecast timestamp. Example: `2026-06-06T13:00:00Z`.                                       | ✅ **Yes — core field.** Becomes `forecast_time_raw`. Useful for preserving the API timestamp.                               |
| `forecast_time_local`                            | Forecast timestamp converted to Norway local time. Example: `2026-06-06T15:00:00+02:00`.                            | ✅ **Yes — core field.** Becomes `forecast_time_local`. Required for joining with electricity prices.                        |
| `local_date`                                     | Norway local date derived from `forecast_time_local`. Example: `2026-06-06`.                                        | ✅ **Yes — core field.** Becomes `date`. Used for joins and filters.                                                         |
| `local_time`                                     | Norway local time derived from `forecast_time_local`. Example: `15:00:00`.                                          | ✅ **Yes — core field.** Becomes `time`. Used for display and analysis.                                                      |
| `local_hour`                                     | Norway local hour derived from `forecast_time_local`. Example: `15`.                                                | ✅ **Yes — core field.** Becomes `hour`. Required for hourly joins with electricity.                                         |
| `local_hour_label`                               | User-friendly hourly interval. Example: `15:00 - 16:00`.                                                            | ✅ **Yes — core field.** Becomes `hour_label`. Useful in Power BI.                                                           |
| `data.instant.details.air_temperature`           | Forecasted air temperature at the exact timestamp. Unit: Celsius. Example: `21.0`.                                  | ✅ **Yes — core field.** Becomes `air_temperature_celsius`. Important because temperature may influence electricity demand.  |
| `data.instant.details.wind_speed`                | Forecasted wind speed at the exact timestamp. Unit: metres per second. Example: `3.8`.                              | ✅ **Yes — core field.** Becomes `wind_speed_mps`. Useful weather and energy context.                                        |
| `data.instant.details.wind_from_direction`       | Direction the wind is coming from, measured in degrees. Example: `190.0`.                                           | 🟡 **Yes — supporting field.** Becomes `wind_from_direction_degrees`. Useful for future weather analysis.                   |
| `data.instant.details.cloud_area_fraction`       | Percentage of sky covered by clouds. Example: `53.5` means 53.5% cloud cover.                                       | 🟡 **Yes — supporting field.** Becomes `cloud_area_fraction_pct`. Useful weather context.                                   |
| `data.instant.details.relative_humidity`         | Moisture level in the air as a percentage. Example: `54.2`.                                                         | 🟡 **Yes — supporting field.** Becomes `relative_humidity_pct`. Useful supporting weather context.                          |
| `data.instant.details.air_pressure_at_sea_level` | Air pressure adjusted to sea level. Unit: hPa. Example: `1011.9`.                                                   | 🟡 **Yes — supporting field.** Becomes `air_pressure_hpa`. Useful for describing weather systems.                           |
| `data.next_1_hours.summary.symbol_code`          | Weather condition code for the next 1 hour. Examples: `clearsky_day`, `partlycloudy_day`, `cloudy`, `rain`.         | ✅ **Yes — core field.** Becomes `weather_symbol_next_1h`. Useful for readable weather labels and tooltips.                  |
| `data.next_1_hours.details.precipitation_amount` | Expected precipitation during the next 1 hour. Unit: millimetres. Example: `0.0`.                                   | ✅ **Yes — core field.** Becomes `precipitation_next_1h_mm`. Best precipitation field because electricity prices are hourly. |
| `data.next_6_hours.summary.symbol_code`          | Weather condition code for the next 6 hours.                                                                        | 🟡 **Yes — supporting field.** Becomes `weather_symbol_next_6h`. Useful for forecast overview pages.                        |
| `data.next_6_hours.details.precipitation_amount` | Expected precipitation during the next 6 hours. Unit: millimetres.                                                  | 🟡 **Yes — supporting field.** Becomes `precipitation_next_6h_mm`. Gives broader precipitation context.                     |
| `data.next_12_hours.summary.symbol_code`         | Weather condition code for the next 12 hours.                                                                       | 🟡 **Yes — optional field.** Becomes `weather_symbol_next_12h`. Useful for high-level forecast context.                     |
| `data.next_12_hours.details`                     | Details for the next 12 hours. In many rows, this can be empty.                                                     | ❌ **No — ignored for MVP.** Often empty and not useful for the first version.                                               |
| `source_file`                                    | Name of the Bronze JSON file that produced the row. Example: `extraction_date=2026-06-06.json`.                     | 🔵 **Yes — metadata field.** Created in Silver as `source_file`. Supports debugging and lineage.                            |
| `processed_at`                                   | Time when our Python transformation processed the row. This is created during Silver transformation.                | 🔵 **Yes — metadata field.** Becomes `processed_at`. Helps track when Silver was created.                                   |

---

## 13. Why these weather fields matter

The weather table gives context around the electricity price.

| Concept           | Field Examples                                           | Why it matters                                   |
| ----------------- | -------------------------------------------------------- | ------------------------------------------------ |
| Temperature       | `air_temperature_celsius`                                | May influence heating demand                     |
| Wind              | `wind_speed_mps`, `wind_from_direction_degrees`          | Gives renewable/weather context                  |
| Cloud cover       | `cloud_area_fraction_pct`                                | Helps describe general weather conditions        |
| Precipitation     | `precipitation_next_1h_mm`                               | Aligns well with hourly price periods            |
| Weather condition | `weather_symbol_next_1h`                                 | Makes dashboard labels more readable             |
| Time              | `forecast_time_utc`, `forecast_time_local`, `local_hour` | Required for correct hourly joins                |
| Location          | `price_area`, `city`, `latitude`, `longitude`            | Connects weather data to electricity price areas |
| Snapshot metadata | `extracted_at_raw`, `extracted_hour`                     | Shows when the forecast was collected            |

---

## 14. Time handling rule: raw + readable timestamps

The electricity and weather APIs use different timestamp styles.

### Electricity API timestamp

Example:

```text
2026-06-06T15:00:00+02:00
```

This is Norway local time. The `+02:00` means Norway is two hours ahead of UTC during summer time.

In Bronze electricity, we keep the original timestamps:

```text
time_start_raw
time_end_raw
```

And we add readable helper fields:

```text
date
start_time
end_time
hour
hour_label
```

---

### Weather API timestamp

Example:

```text
2026-06-06T13:00:00Z
```

This is UTC time. The `Z` means UTC.

In Bronze weather, we keep the original API timestamp:

```text
time
forecast_time_raw
```

And we add Norway local helper fields:

```text
forecast_time_local
local_date
local_time
local_hour
local_hour_label
```

These two timestamps can represent the same real-world moment:

| Weather UTC Time       | Norway Local Time     | Meaning                                |
| ---------------------- | --------------------- | -------------------------------------- |
| `2026-06-06T13:00:00Z` | `2026-06-06 15:00:00` | Same moment, different timezone labels |

In June, Norway uses summer time, so:

```text
13:00 UTC = 15:00 Norway local time
```

This is very important because we join electricity and weather by local date and local hour.

Therefore, in the Silver layer:

* Electricity timestamps are already local
* Weather timestamps are converted from UTC to Norway local time
* The raw API timestamp is still preserved

The final join in the Gold layer should use:

```text
price_area + local date + local hour
```

---

## 15. Final Silver layer outputs

The Silver layer will produce two clean tables.

---

### Silver electricity table

File:

```text
data/silver/silver_electricity_prices.csv
```

Purpose:

```text
Clean hourly electricity price data by price area.
```

Main grain:

```text
One row per price area per hour.
```

Main fields:

```text
source
price_date
extracted_at_raw
extracted_date
extracted_time
timestamp_start_raw
timestamp_end_raw
timestamp_start_local
timestamp_end_local
date
time
hour
hour_label
price_area
price_area_name
nok_per_kwh
eur_per_kwh
exchange_rate
source_file
processed_at
```

---

### Silver weather table

File:

```text
data/silver/silver_weather_forecast.csv
```

Purpose:

```text
Clean weather forecast data by representative city and price area.
```

Main grain:

```text
One row per price area per forecast timestamp.
```

Main fields:

```text
source
extraction_date
extracted_at_raw
extracted_date
extracted_time
extracted_hour
forecast_time_raw
forecast_time_utc
forecast_time_local
date
time
hour
hour_label
price_area
city
latitude
longitude
weather_updated_at_utc
air_temperature_celsius
wind_speed_mps
wind_from_direction_degrees
cloud_area_fraction_pct
relative_humidity_pct
air_pressure_hpa
precipitation_next_1h_mm
weather_symbol_next_1h
precipitation_next_6h_mm
weather_symbol_next_6h
weather_symbol_next_12h
source_file
processed_at
```

---

## 16. Summary

The Bronze layer now stores cleaner daily consolidated JSON files.

Electricity Bronze:

```text
data/bronze/electricity_prices/price_date=YYYY-MM-DD.json
```

Weather Bronze:

```text
data/bronze/weather_forecast/extraction_date=YYYY-MM-DD.json
```

The Silver layer should not blindly copy everything from the raw JSON files.

Instead, it should keep fields that are useful for:

* Hourly electricity price analysis
* Weather impact analysis
* Joining electricity and weather by price area and time
* Power BI dashboard reporting
* Debugging and data lineage

The most important design decision is:

```text
Keep raw API timestamps, but add readable local date/time helper fields.
```

This gives the project both:

* **Traceability** — because raw timestamps are preserved
* **Usability** — because readable date, time, hour, and hour labels are available

For joining electricity and weather, the key rule is:

```text
Convert weather UTC timestamps into Norway local time before joining with electricity prices.
```

This ensures that the weather and electricity data describe the same real-world hour.
