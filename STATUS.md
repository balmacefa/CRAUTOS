# Project Status

## Current State

*   **Submodule Integration:** The repository `balmacefa/crautos_analisis_datos` is successfully integrated as a git submodule in the `crautos_analisis_datos/` directory.
*   **Web Scraper:** The `backend/scrapers/crautos_scraper.py` has been completely rewritten to use **Playwright** asynchronously, replacing the older Selenium implementation. It successfully navigates the CRAutos website, handles pagination, and extracts detailed vehicle information. Tests are passing against the live site.
*   **Machine Learning Predictions:** The `backend/analyzers/price_predictor.py` successfully loads the pre-trained `RandomForestRegressor` model (`car_price_model.pkl`) and its columns (`model_columns.pkl`) from the submodule. The `/api/cars/predict_price` endpoint is functional and returns estimated prices based on vehicle attributes.
*   **Dash Dashboard:** A consolidated Dash application is located in the `dashboard/` directory. It is fully dockerized and integrated into the `docker-compose` files. It fetches live data from the backend API (`/api/cars`) and utilizes the new prediction endpoint for real-time estimations.
*   **Docker Environments:** The `docker-compose.yml`, `docker-compose.dev.yml`, and `docker-compose.prod.yml` files have been updated to include the new `dashboard` service (port 8050) and properly mount the submodule directory so the backend can access the ML models.
*   **Dependencies:** `requirements.txt` and the Dockerfiles have been updated to install `playwright`, `scikit-learn` (v1.7.1), `joblib`, and other necessary libraries.

## Known Limitations

*   **ML Model Path:** The ML model (`car_price_model.pkl`) is loaded directly from the submodule directory (`crautos_analisis_datos/models`). If the submodule is not initialized or the files are missing, the prediction endpoint will fail with a 500 Internal Server Error.
*   **Scraper Concurrency:** The Playwright scraper currently limits concurrency to 10 simultaneous requests using a semaphore. This can be adjusted in the future if needed.
*   **Dashboard Fallback:** If the backend API is unreachable or returns no data, the dashboard will fall back to a "Sin Data" state.
*   **Sync to Async Wrapper:** The `CRAutosScraper.scrape_all_cars()` method is currently wrapped in `asyncio.run()` (with `nest_asyncio`) to maintain compatibility with the existing synchronous backend code. A future refactoring could make the entire scraping pipeline asynchronous.