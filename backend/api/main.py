from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi. middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.database.connection import get_db, init_db, check_db_connection
from backend. database.crud import CarCRUD, ScrapingLogCRUD
from backend.models.schemas import (
    CarResponse, SearchFilters, ReportResponse, ScrapingStatus
)
from backend.analyzers. report_generator import ReportGenerator
from backend.scrapers.crautos_scraper import CRAutosScraper
from backend.models.schemas import CarCreate
from backend.models.ml_schemas import PricePredictionRequest, PricePredictionResponse
from backend.analyzers.price_predictor import price_predictor
from backend.config. settings import settings
from backend.utils.logger import logger
from typing import List
from datetime import datetime
import asyncio


# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="API para análisis de mercado automotriz de CRAutos. com"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting application...")
    init_db()
    if check_db_connection():
        logger.info("Application started successfully")
    else:
        logger.error("Database connection failed")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "CRAutos Market Intelligence API",
        "version": settings.VERSION,
        "docs":  "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        total_cars = CarCRUD. count_cars(db)
        return {
            "status": "healthy",
            "database": "connected",
            "total_cars":  total_cars,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/cars", response_model=List[CarResponse])
async def get_cars(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    db: Session = Depends(get_db)
):
    """Get all cars with pagination"""
    try:
        cars = CarCRUD.get_all_cars(db, skip=skip, limit=limit)
        return cars
    except Exception as e: 
        logger.error(f"Error getting cars: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving cars")


@app.post("/api/cars/search", response_model=List[CarResponse])
async def search_cars(
    filters: SearchFilters,
    db: Session = Depends(get_db)
):
    """Search cars with filters"""
    try:
        cars = CarCRUD.search_cars(db, filters)
        return cars
    except Exception as e:
        logger.error(f"Error searching cars: {e}")
        raise HTTPException(status_code=500, detail="Error searching cars")


@app.get("/api/cars/count")
async def count_cars(db: Session = Depends(get_db)):
    """Get total car count"""
    try:
        total = CarCRUD.count_cars(db)
        return {"total": total}
    except Exception as e:
        logger. error(f"Error counting cars: {e}")
        raise HTTPException(status_code=500, detail="Error counting cars")


@app.get("/api/reports/top-selling", response_model=ReportResponse)
async def get_top_selling_report(db: Session = Depends(get_db)):
    """Get top selling cars report"""
    try: 
        generator = ReportGenerator(db)
        report = generator.generate_top_selling_report()
        return report
    except Exception as e: 
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Error generating report")


@app.get("/api/reports/latest", response_model=ReportResponse)
async def get_latest_report(
    report_type: str = Query("top_selling"),
    db: Session = Depends(get_db)
):
    """Get latest saved report"""
    try:
        generator = ReportGenerator(db)
        report = generator.get_latest_report(report_type)
        if not report:
            raise HTTPException(status_code=404, detail="No report found")
        return report
    except HTTPException: 
        raise
    except Exception as e:
        logger.error(f"Error getting latest report: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving report")


def run_scraping_task(db: Session):
    """Background task to run scraping"""
    log = ScrapingLogCRUD. create_log(db, status="running")
    start_time = datetime.now()
    
    try:
        logger.info("Starting background scraping task...")
        scraper = CRAutosScraper()
        cars_data = scraper.scrape_all_cars()
        
        # Save cars to database
        cars_created = 0
        for car_dict in cars_data:
            try:
                car_create = CarCreate(**car_dict)
                CarCRUD.upsert_car(db, car_create)
                cars_created += 1
            except Exception as e:
                logger.error(f"Error saving car: {e}")
        
        duration = int((datetime.now() - start_time).total_seconds())
        
        ScrapingLogCRUD.update_log(db, str(log. id), {
            'status': 'completed',
            'cars_scraped': cars_created,
            'pages_processed': scraper.max_pages,
            'duration_seconds': duration,
            'finished_at': datetime.now()
        })
        
        logger.info(f"Scraping completed.  Cars saved: {cars_created}")
        
    except Exception as e:
        duration = int((datetime.now() - start_time).total_seconds())
        logger.error(f"Scraping failed: {e}")
        
        ScrapingLogCRUD.update_log(db, str(log.id), {
            'status': 'failed',
            'error_message': str(e),
            'duration_seconds': duration,
            'finished_at': datetime. now()
        })


@app.post("/api/scraper/run")
async def run_scraper(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger scraping process"""
    try:
        background_tasks.add_task(run_scraping_task, db)
        return {
            "message": "Scraping started in background",
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        raise HTTPException(status_code=500, detail="Error starting scraper")


@app.get("/api/scraper/status", response_model=ScrapingStatus)
async def get_scraper_status(db: Session = Depends(get_db)):
    """Get latest scraping status"""
    try: 
        log = ScrapingLogCRUD.get_latest_log(db)
        if not log:
            raise HTTPException(status_code=404, detail="No scraping logs found")
        
        return ScrapingStatus(
            status=log.status,
            cars_scraped=log.cars_scraped,
            pages_processed=log.pages_processed,
            errors_count=log.errors_count,
            duration_seconds=log.duration_seconds,
            started_at=log.started_at,
            finished_at=log. finished_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger. error(f"Error getting scraper status: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving status")


@app.post("/api/cars/predict_price", response_model=PricePredictionResponse)
async def predict_car_price(request: PricePredictionRequest):
    """Predict estimated car price based on attributes using Machine Learning"""
    try:
        estimated_price = price_predictor.predict_price(
            marca=request.marca,
            modelo=request.modelo,
            año=request.año,
            kilometraje=request.kilometraje,
            cilindrada=request.cilindrada,
            combustible=request.combustible,
            transmision=request.transmision,
            cantidad_extras=request.cantidad_extras
        )
        return PricePredictionResponse(
            precio_estimado_crc=estimated_price,
            marca=request.marca,
            modelo=request.modelo,
            año=request.año
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail="Prediction failed")

if __name__ == "__main__": 
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD
    )