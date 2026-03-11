from pydantic import BaseModel, Field
from typing import Optional

class PricePredictionRequest(BaseModel):
    marca: str
    modelo: str
    año: int = Field(..., ge=1900, le=2100)
    kilometraje: float = Field(default=50000, ge=0)
    cilindrada: float = Field(default=1500, ge=0)
    combustible: str = Field(default="Gasolina")
    transmision: str = Field(default="Automática")
    cantidad_extras: int = Field(default=0, ge=0)

class PricePredictionResponse(BaseModel):
    precio_estimado_crc: float
    marca: str
    modelo: str
    año: int
