-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables
CREATE TABLE IF NOT EXISTS cars (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    car_id VARCHAR(100) UNIQUE,
    titulo_completo TEXT NOT NULL,
    marca VARCHAR(100),
    modelo VARCHAR(200),
    año VARCHAR(10),
    precio VARCHAR(50),
    precio_numerico DECIMAL(15, 2),
    transmision VARCHAR(50),
    combustible VARCHAR(50),
    kilometraje VARCHAR(50),
    kilometraje_numerico INTEGER,
    provincia VARCHAR(100),
    estilo VARCHAR(50),
    puertas INTEGER,
    url_detalle TEXT,
    url_imagen TEXT,
    descripcion TEXT,
    vendedor VARCHAR(200),
    telefono VARCHAR(50),
    es_financiado BOOLEAN DEFAULT FALSE,
    recibe_vehiculo BOOLEAN DEFAULT FALSE,
    fecha_publicacion DATE,
    fecha_extraccion TIMESTAMP DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP DEFAULT NOW(),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_cars_marca ON cars(marca);
CREATE INDEX idx_cars_modelo ON cars(modelo);
CREATE INDEX idx_cars_año ON cars(año);
CREATE INDEX idx_cars_precio_numerico ON cars(precio_numerico);
CREATE INDEX idx_cars_fecha_extraccion ON cars(fecha_extraccion);
CREATE INDEX idx_cars_activo ON cars(activo);

-- Create reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_type VARCHAR(50) NOT NULL,
    report_data JSONB NOT NULL,
    total_cars INTEGER,
    fecha_inicio DATE,
    fecha_fin DATE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_reports_type ON reports(report_type);
CREATE INDEX idx_reports_created_at ON reports(created_at);

-- Create scraping_logs table
CREATE TABLE IF NOT EXISTS scraping_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(20) NOT NULL,
    cars_scraped INTEGER DEFAULT 0,
    pages_processed INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    error_message TEXT,
    duration_seconds INTEGER,
    started_at TIMESTAMP DEFAULT NOW(),
    finished_at TIMESTAMP
);

CREATE INDEX idx_scraping_logs_status ON scraping_logs(status);
CREATE INDEX idx_scraping_logs_started_at ON scraping_logs(started_at);