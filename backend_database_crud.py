from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from backend.models.car import Car, Report, ScrapingLog
from backend.models.schemas import CarCreate, SearchFilters
from backend.utils.logger import logger
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json


class CarCRUD: 
    
    @staticmethod
    def create_car(db: Session, car_data: CarCreate) -> Car:
        """Create a new car record"""
        try:
            db_car = Car(**car_data.model_dump())
            db.add(db_car)
            db.commit()
            db.refresh(db_car)
            return db_car
        except Exception as e:
            db.rollback()
            logger. error(f"Error creating car:  {e}")
            raise
    
    @staticmethod
    def bulk_create_cars(db: Session, cars_data: List[CarCreate]) -> int:
        """Bulk create car records"""
        try:
            cars = [Car(**car. model_dump()) for car in cars_data]
            db.bulk_save_objects(cars)
            db.commit()
            logger.info(f"Successfully created {len(cars)} car records")
            return len(cars)
        except Exception as e: 
            db.rollback()
            logger.error(f"Error bulk creating cars: {e}")
            raise
    
    @staticmethod
    def get_car_by_id(db: Session, car_id: str) -> Optional[Car]:
        """Get car by ID"""
        return db.query(Car).filter(Car.car_id == car_id).first()
    
    @staticmethod
    def update_car(db: Session, car_id: str, car_data: dict) -> Optional[Car]:
        """Update car record"""
        try:
            car = db.query(Car).filter(Car.car_id == car_id).first()
            if car:
                for key, value in car_data.items():
                    setattr(car, key, value)
                car.fecha_actualizacion = datetime.now()
                db.commit()
                db.refresh(car)
            return car
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating car: {e}")
            raise
    
    @staticmethod
    def upsert_car(db: Session, car_data: CarCreate) -> Car:
        """Create or update car record"""
        existing_car = CarCRUD.get_car_by_id(db, car_data.car_id)
        if existing_car:
            return CarCRUD.update_car(db, car_data.car_id, car_data. model_dump(exclude_unset=True))
        else:
            return CarCRUD.create_car(db, car_data)
    
    @staticmethod
    def get_all_cars(db: Session, skip: int = 0, limit:  int = 100, active_only: bool = True) -> List[Car]:
        """Get all cars with pagination"""
        query = db.query(Car)
        if active_only:
            query = query.filter(Car.activo == True)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def search_cars(db: Session, filters: SearchFilters) -> List[Car]:
        """Search cars with filters"""
        query = db.query(Car).filter(Car.activo == True)
        
        if filters.marca:
            query = query.filter(Car.marca.ilike(f"%{filters.marca}%"))
        
        if filters.modelo:
            query = query.filter(Car. modelo.ilike(f"%{filters.modelo}%"))
        
        if filters.año_min:
            query = query.filter(Car.año >= str(filters.año_min))
        
        if filters.año_max:
            query = query. filter(Car.año <= str(filters.año_max))
        
        if filters.precio_min:
            query = query.filter(Car.precio_numerico >= filters.precio_min)
        
        if filters.precio_max:
            query = query.filter(Car.precio_numerico <= filters.precio_max)
        
        if filters.transmision:
            query = query.filter(Car.transmision.ilike(f"%{filters.transmision}%"))
        
        if filters.combustible:
            query = query.filter(Car.combustible.ilike(f"%{filters.combustible}%"))
        
        if filters.provincia:
            query = query.filter(Car.provincia.ilike(f"%{filters.provincia}%"))
        
        return query.offset(filters.offset).limit(filters.limit).all()
    
    @staticmethod
    def count_cars(db: Session, active_only: bool = True) -> int:
        """Count total cars"""
        query = db.query(func.count(Car.id))
        if active_only:
            query = query.filter(Car. activo == True)
        return query.scalar()
    
    @staticmethod
    def get_top_marcas(db: Session, limit: int = 10) -> List[Dict]:
        """Get top brands by count"""
        results = db.query(
            Car.marca,
            func.count(Car.id).label('cantidad')
        ).filter(
            Car.activo == True,
            Car.marca.isnot(None),
            Car.marca != ''
        ).group_by(Car.marca).order_by(desc('cantidad')).limit(limit).all()
        
        total = db.query(func.count(Car.id)).filter(Car.activo == True).scalar()
        
        return [
            {
                'marca':  r. marca,
                'cantidad': r.cantidad,
                'porcentaje': round((r.cantidad / total * 100), 2) if total > 0 else 0
            }
            for r in results
        ]
    
    @staticmethod
    def get_top_modelos(db:  Session, limit: int = 20) -> List[Dict]:
        """Get top models by count"""
        results = db.query(
            Car.marca,
            Car.modelo,
            func.count(Car.id).label('cantidad')
        ).filter(
            Car.activo == True,
            Car.marca.isnot(None),
            Car.modelo.isnot(None),
            Car.marca != '',
            Car.modelo != ''
        ).group_by(Car.marca, Car.modelo).order_by(desc('cantidad')).limit(limit).all()
        
        total = db.query(func.count(Car.id)).filter(Car.activo == True).scalar()
        
        return [
            {
                'marca':  r.marca,
                'modelo': r.modelo,
                'modelo_completo': f"{r.marca} {r.modelo}",
                'cantidad': r.cantidad,
                'porcentaje': round((r.cantidad / total * 100), 2) if total > 0 else 0
            }
            for r in results
        ]
    
    @staticmethod
    def get_price_statistics(db: Session) -> Dict:
        """Get price statistics"""
        stats = db.query(
            func.avg(Car.precio_numerico).label('promedio'),
            func.min(Car.precio_numerico).label('minimo'),
            func.max(Car.precio_numerico).label('maximo'),
            func.count(Car.id).label('total')
        ).filter(
            Car.activo == True,
            Car.precio_numerico. isnot(None),
            Car.precio_numerico > 0
        ).first()
        
        # Get median
        subquery = db.query(Car.precio_numerico).filter(
            Car.activo == True,
            Car.precio_numerico.isnot(None),
            Car.precio_numerico > 0
        ).order_by(Car.precio_numerico).subquery()
        
        median = db.query(func.percentile_cont(0.5).within_group(subquery. c.precio_numerico)).scalar()
        
        return {
            'promedio': float(stats.promedio) if stats.promedio else None,
            'mediana': float(median) if median else None,
            'minimo': float(stats.minimo) if stats.minimo else None,
            'maximo': float(stats.maximo) if stats.maximo else None,
            'total_con_precio': stats.total or 0
        }
    
    @staticmethod
    def get_year_distribution(db: Session, limit: int = 10) -> Dict:
        """Get year distribution"""
        results = db.query(
            Car.año,
            func.count(Car.id).label('cantidad')
        ).filter(
            Car.activo == True,
            Car.año.isnot(None),
            Car.año != ''
        ).group_by(Car.año).order_by(desc('cantidad')).limit(limit).all()
        
        return {r.año: r.cantidad for r in results}
    
    @staticmethod
    def get_transmission_distribution(db: Session) -> Dict:
        """Get transmission distribution"""
        results = db. query(
            Car.transmision,
            func.count(Car.id).label('cantidad')
        ).filter(
            Car. activo == True,
            Car.transmision.isnot(None),
            Car.transmision != ''
        ).group_by(Car.transmision).order_by(desc('cantidad')).all()
        
        return {r.transmision: r.cantidad for r in results}
    
    @staticmethod
    def get_fuel_distribution(db: Session) -> Dict:
        """Get fuel type distribution"""
        results = db. query(
            Car.combustible,
            func.count(Car.id).label('cantidad')
        ).filter(
            Car. activo == True,
            Car.combustible.isnot(None),
            Car.combustible != ''
        ).group_by(Car.combustible).order_by(desc('cantidad')).all()
        
        return {r.combustible: r.cantidad for r in results}
    
    @staticmethod
    def deactivate_old_cars(db: Session, days:  int = 30) -> int:
        """Deactivate cars older than specified days"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            updated = db.query(Car).filter(
                Car.fecha_extraccion < cutoff_date,
                Car.activo == True
            ).update({'activo': False})
            
            db.commit()
            logger.info(f"Deactivated {updated} old car records")
            return updated
        except Exception as e:
            db.rollback()
            logger. error(f"Error deactivating old cars: {e}")
            raise


class ReportCRUD: 
    
    @staticmethod
    def create_report(db: Session, report_type: str, report_data: Dict, 
                     total_cars: int, fecha_inicio: date = None, fecha_fin: date = None) -> Report:
        """Create a new report"""
        try:
            db_report = Report(
                report_type=report_type,
                report_data=json.dumps(report_data, ensure_ascii=False),
                total_cars=total_cars,
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin
            )
            db.add(db_report)
            db.commit()
            db.refresh(db_report)
            logger.info(f"Created report: {report_type}")
            return db_report
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating report: {e}")
            raise
    
    @staticmethod
    def get_latest_report(db: Session, report_type: str) -> Optional[Report]:
        """Get latest report by type"""
        return db.query(Report).filter(
            Report.report_type == report_type
        ).order_by(desc(Report.created_at)).first()
    
    @staticmethod
    def get_reports(db: Session, report_type:  str = None, limit: int = 10) -> List[Report]:
        """Get reports with optional type filter"""
        query = db.query(Report)
        if report_type:
            query = query. filter(Report.report_type == report_type)
        return query.order_by(desc(Report.created_at)).limit(limit).all()


class ScrapingLogCRUD:
    
    @staticmethod
    def create_log(db: Session, status: str = "running") -> ScrapingLog:
        """Create a new scraping log"""
        try:
            log = ScrapingLog(status=status)
            db.add(log)
            db.commit()
            db.refresh(log)
            return log
        except Exception as e: 
            db.rollback()
            logger.error(f"Error creating scraping log: {e}")
            raise
    
    @staticmethod
    def update_log(db: Session, log_id: str, updates: Dict) -> Optional[ScrapingLog]:
        """Update scraping log"""
        try: 
            log = db.query(ScrapingLog).filter(ScrapingLog.id == log_id).first()
            if log:
                for key, value in updates.items():
                    setattr(log, key, value)
                db.commit()
                db.refresh(log)
            return log
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating scraping log: {e}")
            raise
    
    @staticmethod
    def get_latest_log(db: Session) -> Optional[ScrapingLog]: 
        """Get latest scraping log"""
        return db.query(ScrapingLog).order_by(desc(ScrapingLog.started_at)).first()
    
    @staticmethod
    def get_logs(db: Session, limit: int = 20) -> List[ScrapingLog]:
        """Get scraping logs"""
        return db.query(ScrapingLog).order_by(desc(ScrapingLog.started_at)).limit(limit).all()