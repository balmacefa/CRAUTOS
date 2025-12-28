from sqlalchemy import Column, String, Integer, Decimal, Boolean, DateTime, Text, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
import uuid

Base = declarative_base()


class Car(Base):
    __tablename__ = "cars"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    car_id = Column(String(100), unique=True, index=True)
    titulo_completo = Column(Text, nullable=False)
    marca = Column(String(100), index=True)
    modelo = Column(String(200))
    año = Column(String(10), index=True)
    precio = Column(String(50))
    precio_numerico = Column(Decimal(15, 2), index=True)
    transmision = Column(String(50))
    combustible = Column(String(50))
    kilometraje = Column(String(50))
    kilometraje_numerico = Column(Integer)
    provincia = Column(String(100))
    estilo = Column(String(50))
    puertas = Column(Integer)
    url_detalle = Column(Text)
    url_imagen = Column(Text)
    descripcion = Column(Text)
    vendedor = Column(String(200))
    telefono = Column(String(50))
    es_financiado = Column(Boolean, default=False)
    recibe_vehiculo = Column(Boolean, default=False)
    fecha_publicacion = Column(Date)
    fecha_extraccion = Column(DateTime(timezone=True), server_default=func.now())
    fecha_actualizacion = Column(DateTime(timezone=True), onupdate=func.now())
    activo = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Car(id={self.id}, marca={self.marca}, modelo={self. modelo}, año={self.año})>"


class Report(Base):
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_type = Column(String(50), nullable=False, index=True)
    report_data = Column(Text, nullable=False)  # JSON string
    total_cars = Column(Integer)
    fecha_inicio = Column(Date)
    fecha_fin = Column(Date)
    created_at = Column(DateTime(timezone=True), server_default=func. now(), index=True)
    
    def __repr__(self):
        return f"<Report(id={self.id}, type={self. report_type}, created_at={self.created_at})>"


class ScrapingLog(Base):
    __tablename__ = "scraping_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(20), nullable=False, index=True)
    cars_scraped = Column(Integer, default=0)
    pages_processed = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    error_message = Column(Text)
    duration_seconds = Column(Integer)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    finished_at = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<ScrapingLog(id={self.id}, status={self.status}, cars={self.cars_scraped})>"