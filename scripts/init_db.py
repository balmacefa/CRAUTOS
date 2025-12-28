#!/usr/bin/env python3
"""
Script to initialize the database
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.connection import init_db, check_db_connection
from backend.utils.logger import logger


def main():
    """Initialize database"""
    logger.info("=" * 50)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 50)
    
    try:
        # Check connection
        logger.info("Checking database connection...")
        if not check_db_connection():
            logger.error("❌ Cannot connect to database")
            logger.error("Please check your database configuration in . env file")
            return False
        
        logger.info("✅ Database connection successful")
        
        # Initialize tables
        logger.info("Creating database tables...")
        init_db()
        logger.info("✅ Database tables created successfully")
        
        logger.info("=" * 50)
        logger.info("✅ DATABASE INITIALIZATION COMPLETED")
        logger.info("=" * 50)
        return True
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)