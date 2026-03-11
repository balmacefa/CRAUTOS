# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Git Submodule:** Integrated `https://github.com/balmacefa/crautos_analisis_datos` as a submodule at `crautos_analisis_datos/` to leverage external data analysis and scraping logic.
- **Playwright Scraper:** Completely rewrote `backend/scrapers/crautos_scraper.py` to use asynchronous `playwright` instead of `selenium`. This enables faster, concurrent, and more reliable extraction of car details from CRAutos.
- **Machine Learning Price Predictions:** Added `backend/analyzers/price_predictor.py` to load the pre-trained `RandomForestRegressor` model (`car_price_model.pkl`) and its features (`model_columns.pkl`) from the submodule.
- **Prediction API Endpoint:** Added a new POST endpoint `/api/cars/predict_price` in `backend/api/main.py` that accepts car attributes (marca, modelo, año, kilometraje, cilindrada, combustible, transmision, cantidad_extras) and returns an estimated price in CRC.
- **Consolidated Dashboard:** Extracted the Dash application from the submodule into a standalone directory (`dashboard/`). The dashboard was refactored to fetch live data from the backend API (`/api/cars`) instead of static CSV files, and to utilize the new `/api/cars/predict_price` endpoint for real-time estimations.
- **Dashboard Dockerization:** Added `dashboard/Dockerfile` to serve the Dash app using Gunicorn.
- **Docker Compose Updates:** Added the `dashboard` service to `docker-compose.yml`, `docker-compose.dev.yml`, and `docker-compose.prod.yml`. Configured the proxy labels in the production compose file to expose the dashboard at `dashboard.${COOLIFY_FQDN}` on port 8050.
- **Dependencies:** Added `playwright`, `nest_asyncio`, `scikit-learn` (v1.7.1), `joblib`, `dash`, `dash-bootstrap-components`, and `gunicorn` to `requirements.txt`. Updated the main `Dockerfile` to run `playwright install chromium`.

### Changed
- Refactored `backend/api/main.py` to handle exceptions and load the new prediction schemas.
- Updated `backend/models/schemas.py` and created `backend/models/ml_schemas.py` to support the new prediction request/response structures.
- Replaced the outdated unit tests in `tests/test_scraper.py` with integration tests that execute the Playwright scraper against the live CRAutos website to validate end-to-end functionality.
- Modified `docker-compose.yml` and `docker-compose.dev.yml` to mount the `crautos_analisis_datos` directory as a volume so the backend container can access the ML model files.
### Fixed (Merge Conflict Resolution)
- **Dashboard Data Fetching:** Updated `dashboard/app.py` to fetch data dynamically via callbacks (`serve_layout()`) on page load and interaction, rather than statically at module load, ensuring the dashboard shows live data.
- **Docker Compose Ports:** Restored backend port mappings (`8000:8000`) in `docker-compose.yml` and `docker-compose.dev.yml` that were lost during the merge, ensuring API endpoints are accessible.
- **HAProxy Routing:** Updated `docker/haproxy.cfg` with ACLs to properly route `/api` traffic to the backend and default all other traffic to the dashboard.
- **Playwright Dependencies:** Added `playwright install-deps` to the `Dockerfile` to ensure all system-level dependencies for Chromium are correctly installed.
