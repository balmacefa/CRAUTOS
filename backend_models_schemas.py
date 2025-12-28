from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


class CarBase(BaseModel):
    car_id: Optional[str] = None
    titulo_completo: str
    marca: Optional[str] = None
    modelo: Optional[str] = None
    año: Optional[str] = None
    precio: Optional[str] = None
    precio_numerico: Optional[Decimal] = None
    transmision: Optional[str] = None
    combustible: Optional[str] = None
    kilometraje: Optional[str] = None
    kilometraje_numerico: Optional[int] = None
    provincia: Optional[str] = None
    estilo: Optional[str] = None
    puertas: Optional[int] = None
    url_detalle: Optional[str] = None
    url_imagen: Optional[str] = None
    descripcion: Optional[str] = None
    vendedor: Optional[str] = None
    telefono: Optional[str] = None
    es_financiado: bool = False
    recibe_vehiculo: bool = False
    fecha_publicacion: Optional[date] = None


class CarCreate(CarBase):
    pass


class CarResponse(CarBase):
    id: str
    fecha_extraccion: datetime
    activo: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TopMarca(BaseModel):
    marca: str
    cantidad: int
    porcentaje: float


class TopModelo(BaseModel):
    marca: str
    modelo: str
    modelo_completo: str
    cantidad: int
    porcentaje: float


class PrecioStats(BaseModel):
    promedio: Optional[float] = None
    mediana: Optional[float] = None
    minimo: Optional[float] = None
    maximo: Optional[float] = None
    total_con_precio: int


class ReportResponse(BaseModel):
    report_type: str
    fecha_generacion: datetime
    total_autos: int
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    top_marcas: List[TopMarca]
    top_modelos: List[TopModelo]
    precios:  PrecioStats
    años_populares: dict
    transmisiones: dict
    combustibles: dict


class ScrapingStatus(BaseModel):
    status: str
    cars_scraped:  int
    pages_processed: int
    errors_count: int
    duration_seconds: Optional[int] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class SearchFilters(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    año_min: Optional[int] = None
    año_max: Optional[int] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None
    transmision: Optional[str] = None
    combustible: Optional[str] = None
    provincia: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)