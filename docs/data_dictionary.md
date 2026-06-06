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

The Silver layer will transform raw JSON into clean tabular datasets that can later be joined in the Gold layer and used in Power BI.

---

## 2. Quick view

| Source            | File Type   | Data Grain                              | Main Use                           |
| ----------------- | ----------- | --------------------------------------- | ---------------------------------- |
| Electricity API ⚡ | JSON list   | One row per price area per hour         | Hourly electricity price analysis  |
| Weather API 🌦️   | Nested JSON | One row per city per forecast timestamp | Weather context for price analysis |

---

## 3. Data flow

```text
⚡ Electricity JSON      🌦️ Weather JSON
        ↓                     ↓
        🥉 Bronze Layer: raw API data
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

The electricity file contains hourly electricity prices for one Norwegian price area and one date.

Example Bronze file:

```text
data/bronze/electricity_prices/2026-06-06_NO1.json
```

This filename tells us:

| Part         | Meaning                          |
| ------------ | -------------------------------- |
| `2026-06-06` | Date of the electricity prices   |
| `NO1`        | Norwegian electricity price area |

The file normally contains around 24 records, one for each hour of the day.

Example record:

```json
{
  "NOK_per_kWh": 1.19029,
  "EUR_per_kWh": 0.10976,
  "EXR": 10.8445,
  "time_start": "2026-06-06T00:00:00+02:00",
  "time_end": "2026-06-06T01:00:00+02:00"
}
```

---

## 6. Electricity data fields

| Raw Field            | Meaning                                                                                                                                                                                            | Use in Silver Layer?                                                                                                                                                                         |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `NOK_per_kWh`        | Electricity price in Norwegian kroner per kilowatt-hour. Example: `1.19029` means 1 kWh costs about 1.19029 NOK during that hour. This is the most understandable price field for Norwegian users. | ✅ **Yes — core field.** Becomes `nok_per_kwh`. Used for average price, max price, min price, hourly price trend, and cheap/expensive hour analysis.                                          |
| `EUR_per_kWh`        | Electricity price in euros per kilowatt-hour. This is useful because Nordic and European electricity markets often use euro-based pricing.                                                         | 🟡 **Yes — supporting field.** Becomes `eur_per_kwh`. Not the main MVP metric, but useful for future European market comparison and validation.                                              |
| `EXR`                | Exchange rate used between EUR and NOK. Example: `10.8445` means 1 EUR is approximately 10.8445 NOK.                                                                                               | 🟡 **Yes — supporting field.** Becomes `exchange_rate`. Helps explain the relationship between EUR and NOK prices.                                                                           |
| `time_start`         | Start timestamp of the hourly electricity price interval. Example: `2026-06-06T00:00:00+02:00`. The `+02:00` means Norway local time is two hours ahead of UTC during summer time.                 | ✅ **Yes — core field.** Becomes `timestamp_start_raw` and `timestamp_start_local`. We also derive `date`, `time`, and `hour` from it. Required for hourly analysis and joining with weather. |
| `time_end`           | End timestamp of the hourly electricity price interval. Example: `2026-06-06T01:00:00+02:00`. Together with `time_start`, this defines the valid price window.                                     | ✅ **Yes — core field.** Becomes `timestamp_end_raw` and `timestamp_end_local`. Used to create `hour_label`, such as `00:00 - 01:00`.                                                         |
| File name date       | Date included in the filename, such as `2026-06-06`. This confirms which date the raw file belongs to.                                                                                             | 🔵 **Optional metadata.** Useful for validation, but the preferred analytical date comes from parsed `time_start`.                                                                           |
| File name price area | Price area included in the filename, such as `NO1`. This is not inside each JSON record, so we extract it from the filename.                                                                       | ✅ **Yes — core field.** Becomes `price_area`. Required for comparing NO1–NO5 and joining with weather data.                                                                                  |
| Price area name      | Human-readable name based on the price area code. Example: `NO1` = Eastern Norway / Oslo. This is added using our own mapping table.                                                               | ✅ **Yes — core field.** Becomes `price_area_name`. Makes Power BI visuals easier to understand.                                                                                              |
| Source file          | Name of the raw JSON file that produced the row. Example: `2026-06-06_NO1.json`.                                                                                                                   | 🔵 **Yes — metadata field.** Becomes `source_file`. Useful for debugging and data lineage.                                                                                                   |
| Processed timestamp  | Time when our Python transformation processed the row. This is not from the API; we create it during transformation.                                                                               | 🔵 **Yes — metadata field.** Becomes `processed_at`. Helps track when the Silver table was created.                                                                                          |

---

## 7. Why these electricity fields matter

The electricity table gives us three essential things:

| Concept                | Field Examples                  | Why it matters                                      |
| ---------------------- | ------------------------------- | --------------------------------------------------- |
| Price                  | `NOK_per_kWh`, `EUR_per_kWh`    | Shows how expensive electricity is during each hour |
| Time                   | `time_start`, `time_end`        | Shows when each price is valid                      |
| Location / market area | `price_area`, `price_area_name` | Allows comparison across Norwegian price areas      |

Together, these fields allow us to answer:

* Which hour is cheapest?
* Which hour is most expensive?
* Which price area has the highest price?
* How do prices change during the day?

---

# Weather Data 🌦️

## 8. Weather data file

### File description

The weather file contains forecast data for one location.

In this project, each electricity price area is represented by one city.

| Price Area | Representative City |
| ---------- | ------------------- |
| NO1        | Oslo                |
| NO2        | Kristiansand        |
| NO3        | Trondheim           |
| NO4        | Tromsø              |
| NO5        | Bergen              |

Example Bronze file:

```text
data/bronze/weather_forecast/2026-06-06_NO1_Oslo.json
```

This filename tells us:

| Part         | Meaning                                      |
| ------------ | -------------------------------------------- |
| `2026-06-06` | Date when the data was extracted             |
| `NO1`        | Electricity price area                       |
| `Oslo`       | Representative city for the weather forecast |

The weather JSON is nested. A simplified structure looks like this:

```text
type
geometry
properties
    ├── meta
    │   ├── updated_at
    │   └── units
    └── timeseries
        ├── time
        └── data
            ├── instant
            │   └── details
            ├── next_1_hours
            ├── next_6_hours
            └── next_12_hours
```

The most important part is:

```text
properties.timeseries
```

Each item inside `timeseries` is one forecast timestamp.

---

## 9. Weather data fields

| Raw Field / Section                              | Meaning                                                                                                                                                | Use in Silver Layer?                                                                                                                                                          |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `type`                                           | Describes the type of object returned by the API. Example: `Feature`. This is API/geospatial metadata.                                                 | ❌ **No — ignored for MVP.** It is not needed for energy or weather analysis in the first version.                                                                             |
| `geometry.coordinates`                           | Location coordinates for the forecast point. Example: `[10.7522, 59.9139, 5]`. The order is longitude, latitude, altitude.                             | 🟡 **Partially yes.** We keep latitude and longitude as `latitude` and `longitude`. Altitude is ignored for the MVP.                                                          |
| `properties.meta.updated_at`                     | Timestamp showing when the weather forecast was last updated by the provider. Example: `2026-06-06T13:27:40Z`. The `Z` means UTC time.                 | 🔵 **Yes — metadata field.** Becomes `weather_updated_at_utc`. Useful for data freshness and pipeline monitoring.                                                             |
| `properties.meta.units`                          | Contains measurement units for weather fields, such as Celsius for temperature, m/s for wind speed, percent for cloud cover, and mm for precipitation. | ❌ **No as a separate field.** Instead, we include units directly in Silver column names, such as `air_temperature_celsius`, `wind_speed_mps`, and `precipitation_next_1h_mm`. |
| `properties.timeseries[].time`                   | Forecast timestamp. Example: `2026-06-06T13:00:00Z`. The `Z` means the time is in UTC.                                                                 | ✅ **Yes — core field.** Becomes `forecast_time_raw`, `forecast_time_utc`, and `forecast_time_local`. We also derive `date`, `time`, and `hour` from the local timestamp.      |
| `data.instant.details.air_temperature`           | Forecasted air temperature at the exact timestamp. Unit: Celsius. Example: `21.0`.                                                                     | ✅ **Yes — core field.** Becomes `air_temperature_celsius`. Important because temperature may influence electricity demand.                                                    |
| `data.instant.details.wind_speed`                | Forecasted wind speed at the exact timestamp. Unit: metres per second. Example: `3.8`.                                                                 | ✅ **Yes — core field.** Becomes `wind_speed_mps`. Wind is useful weather context and may be relevant for energy market analysis.                                              |
| `data.instant.details.wind_from_direction`       | Direction the wind is coming from, measured in degrees. Example: `190.0` means roughly from the south.                                                 | 🟡 **Yes — supporting field.** Becomes `wind_from_direction_degrees`. Kept for completeness and future weather analysis.                                                      |
| `data.instant.details.cloud_area_fraction`       | Percentage of sky covered by clouds. Example: `53.5` means 53.5% cloud cover.                                                                          | 🟡 **Yes — supporting field.** Becomes `cloud_area_fraction_pct`. Gives useful weather context and may support future solar-related analysis.                                 |
| `data.instant.details.relative_humidity`         | Moisture level in the air as a percentage. Example: `54.2` means 54.2% humidity.                                                                       | 🟡 **Yes — supporting field.** Becomes `relative_humidity_pct`. Useful supporting weather context.                                                                            |
| `data.instant.details.air_pressure_at_sea_level` | Air pressure adjusted to sea level. Unit: hPa. Example: `1011.9`.                                                                                      | 🟡 **Yes — supporting field.** Becomes `air_pressure_hpa`. Useful for describing weather systems, though optional for the first dashboard.                                    |
| `data.next_1_hours.summary.symbol_code`          | Short weather condition code for the next 1 hour. Examples: `clearsky_day`, `partlycloudy_day`, `cloudy`, `rain`.                                      | ✅ **Yes — core field.** Becomes `weather_symbol_next_1h`. Useful for readable weather labels and Power BI tooltips.                                                           |
| `data.next_1_hours.details.precipitation_amount` | Expected precipitation during the next 1 hour. Unit: millimetres. Example: `0.0`.                                                                      | ✅ **Yes — core field.** Becomes `precipitation_next_1h_mm`. Best precipitation field for the MVP because electricity prices are also hourly.                                  |
| `data.next_6_hours.summary.symbol_code`          | Weather condition code for the next 6 hours. This gives a medium-term weather summary.                                                                 | 🟡 **Yes — supporting field.** Becomes `weather_symbol_next_6h`. Useful for forecast overview pages, but less important than `next_1_hours`.                                  |
| `data.next_6_hours.details.precipitation_amount` | Expected precipitation during the next 6 hours. Unit: millimetres.                                                                                     | 🟡 **Yes — supporting field.** Becomes `precipitation_next_6h_mm`. Gives broader precipitation context.                                                                       |
| `data.next_12_hours.summary.symbol_code`         | Weather condition code for the next 12 hours. This gives a longer weather summary.                                                                     | 🟡 **Yes — optional field.** Becomes `weather_symbol_next_12h`. Useful for high-level forecast context but not central to hourly analysis.                                    |
| `data.next_12_hours.details`                     | Details for the next 12 hours. In many rows, this is empty.                                                                                            | ❌ **No — ignored for MVP.** Often empty and not useful for the first version.                                                                                                 |
| File name date                                   | Date included in the filename, such as `2026-06-06`. This is the extraction date, not necessarily the forecast date for every row.                     | 🔵 **Optional metadata.** Useful for file tracking, but forecast analysis should use `timeseries[].time`.                                                                     |
| File name price area                             | Price area included in the filename, such as `NO1`. This links the weather city to an electricity price area.                                          | ✅ **Yes — core field.** Becomes `price_area`. Required for joining weather with electricity prices.                                                                           |
| File name city                                   | City included in the filename, such as `Oslo`. This tells us which representative city the forecast belongs to.                                        | ✅ **Yes — core field.** Becomes `city`. Makes the weather data easier to interpret.                                                                                           |
| Source file                                      | Name of the raw JSON file that produced the row. Example: `2026-06-06_NO1_Oslo.json`.                                                                  | 🔵 **Yes — metadata field.** Becomes `source_file`. Supports debugging and data lineage.                                                                                      |
| Processed timestamp                              | Time when our Python transformation processed the row. This is created by our pipeline.                                                                | 🔵 **Yes — metadata field.** Becomes `processed_at`. Helps track when the Silver table was created.                                                                           |

---

## 10. Why these weather fields matter

The weather table gives context around the electricity price.

| Concept           | Field Examples                                  | Why it matters                                   |
| ----------------- | ----------------------------------------------- | ------------------------------------------------ |
| Temperature       | `air_temperature_celsius`                       | May influence heating demand                     |
| Wind              | `wind_speed_mps`, `wind_from_direction_degrees` | Gives renewable/weather context                  |
| Cloud cover       | `cloud_area_fraction_pct`                       | Helps describe general weather conditions        |
| Precipitation     | `precipitation_next_1h_mm`                      | Aligns well with hourly price periods            |
| Weather condition | `weather_symbol_next_1h`                        | Makes dashboard labels more readable             |
| Time              | `forecast_time_utc`, `forecast_time_local`      | Required for correct hourly joins                |
| Location          | `price_area`, `city`, `latitude`, `longitude`   | Connects weather data to electricity price areas |

---

## 11. Time note: UTC vs Norway local time

The electricity and weather APIs use different timestamp styles.

Electricity API example:

```text
2026-06-06T15:00:00+02:00
```

This is Norway local time. The `+02:00` means Norway is two hours ahead of UTC during summer time.

Weather API example:

```text
2026-06-06T13:00:00Z
```

This is UTC time. The `Z` means UTC.

These two timestamps can represent the same real-world moment:

| Weather UTC Time       | Norway Local Time     | Meaning                                |
| ---------------------- | --------------------- | -------------------------------------- |
| `2026-06-06T13:00:00Z` | `2026-06-06 15:00:00` | Same moment, different timezone labels |

In June, Norway uses summer time, so:

```text
13:00 UTC = 15:00 Norway local time
```

This is very important because we will join electricity and weather by local date and local hour.

Therefore, in the Silver layer:

* Electricity timestamps are already local
* Weather timestamps must be converted from UTC to Norway local time

The final join in the Gold layer should use:

```text
price_area + local date + local hour
```

---

## 12. Final Silver layer outputs

The Silver layer will produce two clean tables.

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
forecast_time_utc
forecast_time_local
date
time
hour
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

## 13. Summary

The Silver layer should not blindly copy everything from the raw JSON files.

Instead, it should keep fields that are useful for:

* Hourly electricity price analysis
* Weather impact analysis
* Joining electricity and weather by price area and time
* Power BI dashboard reporting
* Debugging and data lineage

The most important design decision is:

```text
Convert weather UTC timestamps into Norway local time before joining with electricity prices.
```

This ensures that the weather and electricity data describe the same real-world hour.

---

