import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from backend.scrapers.crautos_scraper import CRAutosScraper

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
