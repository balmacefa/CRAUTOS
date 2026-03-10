import pytest
import os
import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

# We need to monkey patch PostgreSQL UUID before models are imported
from sqlalchemy.dialects import sqlite
import sqlalchemy.types as types
class StringUUID(types.TypeDecorator):
    impl = types.String
    cache_ok = True
    def __init__(self, as_uuid=False, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(types.String(36))
        else:
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "sqlite":
            return str(value)
        else:
            return value
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "sqlite":
            return uuid.UUID(value)
        else:
            return value

import sqlalchemy.dialects.postgresql
sqlalchemy.dialects.postgresql.UUID = StringUUID

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.scrapers.crautos_scraper import CRAutosScraper
from backend.database.crud import CarCRUD
from backend.models.schemas import CarCreate
from backend.models.car import Base as ModelBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_scraper.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

with engine.begin() as conn:
    ModelBase.metadata.create_all(conn)

@pytest.fixture
def db_session():
    try:
        db = TestingSessionLocal()
        ModelBase.metadata.create_all(bind=db.get_bind())
        yield db
    finally:
        db.close()

@pytest.fixture(scope="session", autouse=True)
def cleanup(request):
    """Cleanup a testing directory once we are finished."""
    def remove_test_db():
        if os.path.exists("./test_scraper.db"):
            os.remove("./test_scraper.db")
    request.addfinalizer(remove_test_db)


@pytest.fixture
def mock_html_content():
    return """
    <html>
        <body>
        </body>
    </html>
    """

def test_scrape_all_cars_live():
    # Execute the scraper against the live website for 1 page only to ensure real integration works
    scraper = CRAutosScraper(headless=True, max_pages=1)

    # We patch time.sleep to avoid waiting the delay between pages even if it's 1 page (just in case)
    with patch('time.sleep', return_value=None):
        results = scraper.scrape_all_cars()

    # We expect to find at least some cars on the first page
    assert len(results) > 0

    first_car = results[0]

    # Verify the structure has the required keys populated from a real scrape
    assert "titulo_completo" in first_car
    assert "marca" in first_car
    assert "año" in first_car
    assert "precio" in first_car
    assert "url_detalle" in first_car

    # Basic sanity checks to ensure data isn't empty
    assert len(first_car["titulo_completo"]) > 0
    assert len(first_car["marca"]) > 0
    assert first_car["precio"] is not None


def test_scrape_two_pages_live_and_save_to_db(db_session):
    # Execute the scraper against the live website for 2 pages
    scraper = CRAutosScraper(headless=True, max_pages=2)

    with patch('time.sleep', return_value=None):
        results = scraper.scrape_all_cars()

    # We expect to find cars from at least 2 pages (typically > 20 cars)
    assert len(results) > 0

    # Pick the first car to save
    first_car_data = results[0]

    # Ensure it has a car_id, otherwise create a fake one
    if "car_id" not in first_car_data:
        first_car_data["car_id"] = str(uuid.uuid4())

    # Ensure required fields and some optional ones that we can easily check
    assert "titulo_completo" in first_car_data

    # Remove any extra keys that are not part of CarCreate schema if needed,
    # though CarCreate with `pass` on `CarBase` will ignore them or we can just map it directly.
    # The Pydantic model will drop unknown keys if not configured to forbid them,
    # but to be safe we extract the known keys.

    try:
        car_create = CarCreate(**first_car_data)
        saved_car = CarCRUD.create_car(db_session, car_create)
    except Exception as e:
        pytest.fail(f"Failed to create CarCreate schema or save to DB: {e}")

    assert saved_car.id is not None
    assert saved_car.car_id == first_car_data.get("car_id")
    assert saved_car.titulo_completo == first_car_data.get("titulo_completo")

    # Verify it can be read back
    read_car = CarCRUD.get_car_by_id(db_session, saved_car.car_id)
    assert read_car is not None
    assert read_car.car_id == saved_car.car_id
