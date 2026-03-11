# Procedures and Operations

## 1. Initial Setup and Updating

### Cloning the Repository

To clone the repository and initialize the `crautos_analisis_datos` submodule, run:

```bash
git clone --recurse-submodules <repository-url>
```

If the repository has already been cloned without the submodule, initialize it by running:

```bash
git submodule update --init --recursive
```

### Updating the Submodule

To pull the latest changes from the `crautos_analisis_datos` external repository:

```bash
git submodule update --remote crautos_analisis_datos
```

If the ML models (`car_price_model.pkl`, `model_columns.pkl`) or the Dash dashboard code are updated in the external repository, you must re-build the Docker images to pick up the changes.

---

## 2. Running the Application via Docker Compose

### Development Environment

The development environment mounts the source code and the submodule directory for hot-reloading.

```bash
docker-compose -f docker-compose.dev.yml up --build
```

- **Backend API:** Available at `http://localhost:8000/docs`
- **Dash Dashboard:** Available at `http://localhost:8050`

### Production Environment (Coolify/Traefik)

The production environment uses the pre-built images and relies on an internal proxy (like Coolify's Traefik or Caddy) to handle external routing.

```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

- **Backend API:** Internal to the Docker network (`http://backend:8000`)
- **Proxy:** Exposed on port 80 (configured via labels)
- **Dash Dashboard:** Exposed internally on port 8050, routed via Traefik labels (`dashboard.${COOLIFY_FQDN}`).

---

## 3. Machine Learning Price Prediction

The backend API exposes a new endpoint for estimating car prices based on a Random Forest ML model.

### API Endpoint: `/api/cars/predict_price`

**Method:** `POST`

**Request Body (JSON):**
```json
{
  "marca": "Toyota",
  "modelo": "Corolla",
  "año": 2018,
  "kilometraje": 50000,
  "cilindrada": 1800,
  "combustible": "Gasolina",
  "transmision": "Automática",
  "cantidad_extras": 0
}
```

**Response (JSON):**
```json
{
  "precio_estimado_crc": 8500000.0,
  "marca": "Toyota",
  "modelo": "Corolla",
  "año": 2018
}
```

### Loading the ML Model

The `PricePredictor` class (`backend/analyzers/price_predictor.py`) automatically loads the `.pkl` files from the mounted `crautos_analisis_datos/models` directory upon backend startup. Ensure this directory is mounted correctly in the Docker Compose configuration.

---

## 4. Playwright Scraper

The `CRAutosScraper` (`backend/scrapers/crautos_scraper.py`) now uses asynchronous Playwright to extract vehicle data.

### Configuration

- **Headless Mode:** Controlled by the `SCRAPER_HEADLESS` environment variable (default: `True`).
- **Max Pages:** Controlled by `SCRAPER_MAX_PAGES`. The scraper will attempt to find the total number of pages on the CRAutos site, but will stop at this limit.

### Running the Scraper

The scraper can be triggered via the background task endpoint:

```bash
curl -X POST http://localhost:8000/api/scraper/run
```

You can check the status of the scraping job at `/api/scraper/status`.

---

## 5. Dash Dashboard

The Dash dashboard is served by the `dashboard` container using Gunicorn (`dashboard/Dockerfile`).

- It fetches live vehicle data from the backend API (`http://backend:8000/api/cars`).
- It uses the ML endpoint (`/api/cars/predict_price`) to estimate prices interactively.
- The base API URL is configurable via the `API_URL` environment variable.