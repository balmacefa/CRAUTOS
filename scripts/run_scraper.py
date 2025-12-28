#!/usr/bin/env python3
"""
Script to run the CRAutos scraper
"""
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.scrapers.crautos_scraper import CRAutosScraper
from backend.database.connection import SessionLocal
from backend.database.crud import CarCRUD, ScrapingLogCRUD
from backend.models.schemas import CarCreate
from backend.utils.logger import logger
import argparse


def main(max_pages: int = None, headless: bool = True):
    """Run scraper and save to database"""
    logger.info("=" * 50)
    logger.info("CRAUTOS SCRAPER")
    logger.info("=" * 50)
    
    db = SessionLocal()
    log = ScrapingLogCRUD.create_log(db, status="running")
    start_time = datetime.now()
    
    try:
        # Initialize scraper
        logger.info(f"Initializing scraper (headless={headless}, max_pages={max_pages})...")
        scraper = CRAutosScraper(headless=headless, max_pages=max_pages)
        
        # Scrape cars
        logger.info("Starting scraping process...")
        cars_data = scraper.scrape_all_cars()
        
        logger.info(f"✅ Scraped {len(cars_data)} cars")
        
        # Save to database
        logger.info("Saving cars to database...")
        cars_created = 0
        cars_updated = 0
        errors = 0
        
        for i, car_dict in enumerate(cars_data, 1):
            try:
                car_create = CarCreate(**car_dict)
                existing = CarCRUD.get_car_by_id(db, car_create.car_id)
                
                if existing:
                    CarCRUD.update_car(db, car_create. car_id, car_dict)
                    cars_updated += 1
                else:
                    CarCRUD.create_car(db, car_create)
                    cars_created += 1
                
                if i % 50 == 0:
                    logger.info(f"Progress: {i}/{len(cars_data)} cars processed")
                    
            except Exception as e: 
                errors += 1
                logger.error(f"Error saving car {i}: {e}")
        
        duration = int((datetime. now() - start_time).total_seconds())
        
        # Update log
        ScrapingLogCRUD.update_log(db, str(log.id), {
            'status': 'completed',
            'cars_scraped': cars_created + cars_updated,
            'pages_processed': scraper.max_pages,
            'errors_count': errors,
            'duration_seconds': duration,
            'finished_at': datetime.now()
        })
        
        logger. info("=" * 50)
        logger.info("✅ SCRAPING COMPLETED")
        logger.info(f"📊 New cars:  {cars_created}")
        logger.info(f"🔄 Updated cars: {cars_updated}")
        logger.info(f"❌ Errors: {errors}")
        logger.info(f"⏱️  Duration: {duration} seconds")
        logger.info("=" * 50)
        
        return True
        
    except Exception as e:
        duration = int((datetime.now() - start_time).total_seconds())
        logger.error(f"❌ Scraping failed: {e}")
        
        ScrapingLogCRUD.update_log(db, str(log.id), {
            'status': 'failed',
            'error_message': str(e),
            'duration_seconds': duration,
            'finished_at':  datetime.now()
        })
        
        return False
        
    finally:
        db. close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run CRAutos scraper')
    parser.add_argument('--max-pages', type=int, default=None, help='Maximum pages to scrape')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in visible mode')
    
    args = parser.parse_args()
    
    success = main(max_pages=args.max_pages, headless=not args.no_headless)
    sys.exit(0 if success else 1)