# Norway Energy Intelligence Platform

An end-to-end data analytics project for the Norwegian energy sector using Python, Apache Airflow, dbt, Microsoft Fabric, and Power BI.

## Project Goal

This project collects Norwegian electricity price data and weather forecast data, processes it through a Bronze, Silver, and Gold data architecture, and creates analytics-ready datasets for Power BI dashboards.

## Data Sources

- Electricity prices: Hva koster strømmen API
- Weather forecast: MET Norway Locationforecast API

## Architecture

API sources  
→ Bronze raw JSON  
→ Silver cleaned tables  
→ Gold analytics mart  
→ Power BI dashboard