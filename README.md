# 🚗 CRAutos Market Intelligence System

Sistema completo de análisis de mercado automotriz para **CRAutos. com** - El portal líder de autos usados en Costa Rica.

## 🎯 Características

✅ **Web Scraping Avanzado** - Extrae datos de miles de autos automáticamente  
✅ **API REST** - Endpoints para consultar y analizar datos  
✅ **Base de Datos PostgreSQL** - Almacenamiento robusto y escalable  
✅ **Reportes Inteligentes** - Análisis de autos más vendidos, precios, tendencias  
✅ **Docker** - Deployment fácil y rápido  
✅ **Automatización** - Scraping y reportes programados  

---

## 📊 ¿Qué hace este sistema?

Este sistema te permite:

1. 🔍 **Extraer** todos los autos publicados en CRAutos.com
2. 💾 **Almacenar** los datos en una base de datos PostgreSQL
3. 📈 **Analizar** tendencias de mercado, marcas más populares, precios
4. 📊 **Generar reportes** de autos más vendidos con estadísticas detalladas
5. 🔌 **Consultar** datos vía API REST

---

## 🚀 Instalación Rápida con Docker

### Prerequisitos

- Docker y Docker Compose instalados
- 4GB de RAM mínimo
- Puerto 8000 disponible

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/Sebas10CR/CRAUTOS. git
cd CRAUTOS

# 2. Crear archivo .env
cp .env. example .env

# 3. Levantar los servicios
docker-compose up -d

# 4. Ver logs
docker-compose logs -f backend

# 5. Acceder a la API
# http://localhost:8000/docs
```

**¡Listo!** 🎉 La API estará disponible en `http://localhost:8000`

---

## 🖥️ Instalación Manual (Sin Docker)

### Prerequisitos

- Python 3.11+
- PostgreSQL 15+
- Chrome/Chromium instalado

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/Sebas10CR/CRAUTOS.git
cd CRAUTOS

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp . env.example .env
# Editar .env con tus credenciales de PostgreSQL

# 5. Inicializar base de datos
python scripts/init_db.py

# 6. Ejecutar scraper
python scripts/run_scraper.py --max-pages 10

# 7. Generar reporte
python scripts/generate_report.py

# 8. Iniciar API
python backend/api/main.py
```

---

## 📖 Uso

### 1️⃣ Ejecutar Scraper

```bash
# Con Docker
docker-compose exec backend python scripts/run_scraper.py --max-pages 20

# Sin Docker
python scripts/run_scraper.py --max-pages 20

# Ver browser mientras funciona (no headless)
python scripts/run_scraper.py --no-headless --max-pages 5
```

### 2️⃣ Generar Reporte

```bash
# Generar reporte JSON
python scripts/generate_report. py --format json

# Generar reporte CSV
python scripts/generate_report.py --format csv --output reporte_custom.csv
```

### 3️⃣ Usar la API

```bash
# Ver documentación interactiva
http://localhost:8000/docs

# Obtener todos los autos (paginado)
curl http://localhost:8000/api/cars?limit=100

# Buscar autos
curl -X POST http://localhost:8000/api/cars/search \
  -H "Content-Type: application/json" \
  -d '{
    "marca": "Toyota",
    "año_min": 2018,
    "año_max":  2023,
    "precio_max": 15000000
  }'

# Obtener reporte de autos más vendidos
curl http://localhost:8000/api/reports/top-selling

# Iniciar scraping
curl -X POST http://localhost:8000/api/scraper/run

# Ver estado del scraper
curl http://localhost:8000/api/scraper/status
```

---

## 🌐 Endpoints de la API

### **GET** `/api/cars`
Obtener lista de autos con paginación

**Parámetros:**
- `skip` (int): Registros a saltar (default: 0)
- `limit` (int): Máximo de registros (default: 100)

### **POST** `/api/cars/search`
Buscar autos con filtros avanzados

**Body:**
```json
{
  "marca": "Toyota",
  "modelo": "Corolla",
  "año_min": 2018,
  "año_max":  2023,
  "precio_min": 5000000,
  "precio_max": 15000000,
  "transmision": "Automática",
  "combustible":  "Gasolina",
  "provincia": "San José",
  "limit": 100,
  "offset": 0
}
```

### **GET** `/api/reports/top-selling`
Generar reporte de autos más vendidos

**Respuesta:**
```json
{
  "report_type": "top_selling",
  "fecha_generacion": "2025-12-28T10:30:00",
  "total_autos": 2547,
  "top_marcas": [
    {
      "marca":  "Toyota",
      "cantidad":  456,
      "porcentaje":  17.9
    },
    {
      "marca": "Honda",
      "cantidad": 312,
      "porcentaje":  12.2
    }
  ],
  "top_modelos":  [
    {
      "marca": "Toyota",
      "modelo":  "Corolla",
      "modelo_completo": "Toyota Corolla",
      "cantidad": 89,
      "porcentaje":  3.5
    }
  ],
  "precios": {
    "promedio":  8750000.50,
    "mediana": 7500000.00,
    "minimo": 1200000.00,
    "maximo": 45000000.00
  },
  "años_populares":  {
    "2020": 312,
    "2019": 298,
    "2021": 276
  }
}
```

### **POST** `/api/scraper/run`
Iniciar proceso de scraping en background

### **GET** `/api/scraper/status`
Ver estado del último scraping

---

## 📁 Estructura del Proyecto

```
CRAUTOS/
├── backend/
│   ├── api/              # FastAPI endpoints
│   │   └── main.py
│   ├── scrapers/         # Web scraping logic
│   │   └── crautos_scraper.py
│   ├── database/         # Database connection & CRUD
│   │   ├── connection.py
│   │   └── crud.py
│   ├── models/           # SQLAlchemy & Pydantic models
│   │   ├── car.py
│   │   └── schemas.py
│   ├── analyzers/        # Report generation
│   │   └── report_generator.py
│   ├── config/           # Configuration
│   │   └── settings. py
│   └── utils/            # Utilities (logger, etc.)
│       └── logger.py
├── scripts/              # Utility scripts
│   ├── init_db.py
│   ├── run_scraper.py
│   └── generate_report.py
├── docker/               # Docker configs
│   ├── Dockerfile
│   └── postgres/
│       └── init. sql
├── logs/                 # Application logs
├── reports/              # Generated reports
├── docker-compose.yml
├── requirements.txt
├── . env.example
└── README. md
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno (. env)

```bash
# Database
DATABASE_URL=postgresql://crautos_user:crautos_pass@localhost: 5432/crautos_db

# Scraper
SCRAPER_HEADLESS=True
SCRAPER_MAX_PAGES=50
SCRAPER_DELAY_SECONDS=2

# API
API_HOST=0.0.0.0
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

### Programar Scraping Automático

Agregar a crontab (Linux/Mac):

```bash
# Ejecutar scraper todos los días a las 2 AM
0 2 * * * cd /path/to/CRAUTOS && docker-compose exec -T backend python scripts/run_scraper.py --max-pages 50

# Generar reporte todos los días a las 8 AM
0 8 * * * cd /path/to/CRAUTOS && docker-compose exec -T backend python scripts/generate_report.py
```

---

## 📊 Ejemplo de Reporte

```
📊 REPORT SUMMARY
==================================================
Total Cars: 2547

🏆 Top 5 Brands:
  1. Toyota: 456 (17.9%)
  2. Honda: 312 (12.2%)
  3. Nissan: 289 (11.3%)
  4. Hyundai: 245 (9.6%)
  5. Mazda: 198 (7.8%)

🔥 Top 10 Models:
  1. Toyota Corolla: 89 (3.5%)
  2. Honda CR-V: 76 (3.0%)
  3. Nissan Sentra: 65 (2.6%)
  4. Toyota RAV4: 58 (2.3%)
  5. Honda Civic: 54 (2.1%)
  6. Mazda 3: 48 (1.9%)
  7. Hyundai Tucson: 45 (1.8%)
  8. Toyota Yaris: 42 (1.6%)
  9. Nissan X-Trail: 39 (1.5%)
  10. Honda Accord: 37 (1.5%)

💰 Price Statistics: 
  Average: ₡8,750,000.50
  Median: ₡7,500,000.00
  Min: ₡1,200,000.00
  Max: ₡45,000,000.00

📅 Top 5 Years: 
  2020: 312 cars
  2019: 298 cars
  2021: 276 cars
  2018: 245 cars
  2022: 198 cars
```

---

## 🐛 Troubleshooting

### Error: Database connection failed

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps

# Ver logs de PostgreSQL
docker-compose logs postgres

# Recrear servicios
docker-compose down -v
docker-compose up -d
```

### Error: Chrome driver not found

```bash
# Instalar Chrome en el contenedor
docker-compose exec backend apt-get update
docker-compose exec backend apt-get install -y chromium chromium-driver
```

### Error: Permission denied

```bash
# Dar permisos a los scripts
chmod +x scripts/*. py
```

---

## 🤝 Contribuciones

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto es de código abierto bajo la licencia MIT.

---

## 👤 Autor

**Sebas10CR**

- GitHub: [@Sebas10CR](https://github.com/Sebas10CR)

---

## ⭐ ¿Te gusta el proyecto?

¡Dale una estrella en GitHub! ⭐

---

## 📧 Soporte

¿Tienes preguntas o necesitas ayuda?  Abre un issue en GitHub. 

---

## 🗺️ Roadmap

- [ ] Dashboard web interactivo
- [ ] Alertas de precios
- [ ] Comparador de precios históricos
- [ ] ML para predicción de precios
- [ ] Notificaciones por email
- [ ] Exportar reportes a PDF
- [ ] Integración con WhatsApp

---

**Hecho con ❤️ en Costa Rica** 🇨🇷