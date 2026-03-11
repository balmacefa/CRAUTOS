import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
import os


from backend.api.main import app
from backend.database.connection import Base, get_db
from backend.models.car import Car, Report, ScrapingLog, Base as ModelBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

with engine.begin() as conn:
    ModelBase.metadata.create_all(conn)

def override_get_db():
    try:
        db = TestingSessionLocal()
        # Create tables on every connection just in case
        ModelBase.metadata.create_all(bind=db.get_bind())
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert response.json()["message"] == "CRAutos Market Intelligence API"

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "total_cars" in response.json()

def test_get_cars_empty():
    response = client.get("/api/cars")
    assert response.status_code == 200
    assert response.json() == []

def test_count_cars_empty():
    response = client.get("/api/cars/count")
    assert response.status_code == 200
    assert response.json() == {"total": 0}

def test_scraper_status_not_found():
    response = client.get("/api/scraper/status")
    # By default, since the DB is empty, this should return 404
    assert response.status_code == 404
    assert response.json()["detail"] == "No scraping logs found"

# Clean up after tests (optional but good practice)
@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""
    def remove_test_db():
        import os
        if os.path.exists("./test.db"):
            os.remove("./test.db")
    request.addfinalizer(remove_test_db)
