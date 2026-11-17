# GridGuard AI
AI-powered electricity monitoring and analytics major-project prototype.

## Requirements
- Python 3.10+
- Internet connection only if you want to load the Chart.js CDN on first use (or replace it with a local copy).

## Run on Windows
1. Extract the ZIP.
2. Double-click `setup.bat` (creates a virtual environment and installs dependencies).
3. Double-click `run.bat`.
4. Open http://127.0.0.1:5000

## Run on macOS/Linux
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Demo accounts
- Admin: `admin@gridguard.ai` / `Admin@123`
- Consumer: `user@gridguard.ai` / `User@123`

Change the development secret and demo passwords before any real deployment.

## Modules
- Consumption dashboard and smart meter registry
- Isolation Forest anomaly screening
- Historical outage-pattern risk estimate
- Random Forest daily demand forecast
- Tariff-based bill estimator
- Rule-based energy recommendations
- Alerts, complaints API and PDF summary report

## Important research limitations
This is a software-only demonstration using synthetic CSV data. The anomaly detector identifies unusual readings, not confirmed theft. Outage risk is an experimental model using limited historical records, not a live grid reliability forecast. The bill calculator uses an illustrative flat tariff and must be configured with the applicable DISCOM tariff before practical use.

## Data
`data/sample_consumption.csv` contains 90 days of simulated readings for 100 meters.
`data/sample_outages.csv` contains simulated area outage and weather records.

The SQLite database is created automatically on first run and seeded from the CSV files.


### Energy waste prediction module
Open **Energy waste prediction** from the sidebar. It compares each meter's latest 7-day average with its preceding 21-day median, flags increases of 10% or more, and estimates the extra kWh over the next 7 days if the recent pattern continues. These are potential excess-use indicators, not proof of waste; weather, occupancy and operating changes should be checked.
