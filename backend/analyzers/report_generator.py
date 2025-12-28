from sqlalchemy. orm import Session
from backend.database.crud import CarCRUD, ReportCRUD
from backend.models.schemas import ReportResponse, TopMarca, TopModelo, PrecioStats
from backend.utils.logger import logger
from datetime import datetime, date
from typing import Optional
import json


class ReportGenerator:
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_top_selling_report(self, 
                                    fecha_inicio: Optional[date] = None,
                                    fecha_fin: Optional[date] = None) -> ReportResponse:
        """Generate comprehensive top selling cars report"""
        
        logger.info("Generating top selling report...")
        
        try:
            # Get total cars
            total_cars = CarCRUD.count_cars(self.db)
            
            # Get top brands
            top_marcas_data = CarCRUD.get_top_marcas(self.db, limit=10)
            top_marcas = [TopMarca(**m) for m in top_marcas_data]
            
            # Get top models
            top_modelos_data = CarCRUD. get_top_modelos(self.db, limit=20)
            top_modelos = [TopModelo(**m) for m in top_modelos_data]
            
            # Get price statistics
            precios_data = CarCRUD.get_price_statistics(self.db)
            precios = PrecioStats(**precios_data)
            
            # Get year distribution
            años_populares = CarCRUD.get_year_distribution(self.db, limit=10)
            
            # Get transmission distribution
            transmisiones = CarCRUD.get_transmission_distribution(self.db)
            
            # Get fuel distribution
            combustibles = CarCRUD.get_fuel_distribution(self.db)
            
            report = ReportResponse(
                report_type="top_selling",
                fecha_generacion=datetime.now(),
                total_autos=total_cars,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                top_marcas=top_marcas,
                top_modelos=top_modelos,
                precios=precios,
                años_populares=años_populares,
                transmisiones=transmisiones,
                combustibles=combustibles
            )
            
            # Save report to database
            report_dict = report.model_dump(mode='json')
            ReportCRUD.create_report(
                self.db,
                report_type="top_selling",
                report_data=report_dict,
                total_cars=total_cars,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            
            logger.info("Top selling report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise
    
    def export_report_to_json(self, report:  ReportResponse, filename: str):
        """Export report to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report.model_dump(mode='json'), f, indent=2, ensure_ascii=False, default=str)
            logger. info(f"Report exported to {filename}")
        except Exception as e:
            logger.error(f"Error exporting report to JSON: {e}")
            raise
    
    def get_latest_report(self, report_type: str = "top_selling") -> Optional[ReportResponse]:
        """Get latest report from database"""
        try:
            report = ReportCRUD.get_latest_report(self.db, report_type)
            if report:
                report_data = json.loads(report.report_data)
                return ReportResponse(**report_data)
            return None
        except Exception as e:
            logger.error(f"Error getting latest report: {e}")
            return None