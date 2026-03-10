import pytest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from backend.scrapers.crautos_scraper import CRAutosScraper

@pytest.fixture
def mock_html_content():
    return """
    <html>
        <body>
            <div class="inventory">
                <div class="title">Toyota Corolla 2018</div>
                <a href="/autosusados/detalles.cfm?id=123456">Ver detalles</a>
                <div class="price">¢ 8,500,000</div>
                <img class="preview" src="http://example.com/image.jpg" />
                <table class="options-primary">
                    <tr><td>Transmisión: Automática</td></tr>
                    <tr><td>Combustible: Gasolina</td></tr>
                    <tr><td>Kilometraje: 50,000 km</td></tr>
                    <tr><td>Estilo: Sedán</td></tr>
                    <tr><td>Puertas: 4 puertas</td></tr>
                    <tr><td>Provincia: San José</td></tr>
                </table>
                <div class="seller-name">Agencia de Autos S.A.</div>
                <div class="phone">8888-8888</div>
            </div>
            <div class="inventory">
                <div class="title">Honda Civic 2020</div>
                <a href="/autosusados/detalles.cfm?id=654321">Ver detalles</a>
                <div class="price">$ 15,000.50</div>
                <img class="preview" src="http://example.com/honda.jpg" />
                <table class="options-primary">
                    <tr><td>Transmisión: Manual</td></tr>
                    <tr><td>Combustible: Híbrido</td></tr>
                    <tr><td>Kilometraje: 10,000 km</td></tr>
                    <tr><td>Puertas: 5 puertas</td></tr>
                    <tr><td>Provincia: Alajuela</td></tr>
                </table>
                <div class="seller-name">Juan Pérez</div>
                <div class="phone">9999-9999</div>
            </div>
        </body>
    </html>
    """

def test_scraper_parse_title():
    scraper = CRAutosScraper(headless=True, max_pages=1)

    # Test typical structure: Brand Model Model Year
    parsed1 = scraper._parse_title("Toyota Corolla 2018")
    assert parsed1["marca"] == "Toyota"
    assert parsed1["modelo"] == "Corolla"
    assert parsed1["año"] == "2018"

    # Test structure with multiple model words
    parsed2 = scraper._parse_title("Nissan Sentra B13 1999")
    assert parsed2["marca"] == "Nissan"
    assert parsed2["modelo"] == "Sentra B13"
    assert parsed2["año"] == "1999"

    # Test edge case: missing year
    parsed3 = scraper._parse_title("Honda")
    assert parsed3["marca"] == "Honda"
    assert parsed3["modelo"] == ""
    assert parsed3["año"] == ""

def test_scraper_parse_price():
    scraper = CRAutosScraper(headless=True, max_pages=1)

    assert scraper._parse_price("¢ 8,500,000") == 8500000.0
    assert scraper._parse_price("$ 15,000.50") == 15000.50
    assert scraper._parse_price("Precio a convenir") == None
    assert scraper._parse_price("10.000,50") == 10000.50

def test_extract_attributes(mock_html_content):
    scraper = CRAutosScraper(headless=True, max_pages=1)
    soup = BeautifulSoup(mock_html_content, 'html.parser')
    options_table = soup.find('table', class_='options-primary')

    attributes = scraper._extract_attributes(options_table)

    assert attributes.get("transmision") == "Automática"
    assert attributes.get("combustible") == "Gasolina"
    assert attributes.get("kilometraje") == "50,000 km"
    assert attributes.get("kilometraje_numerico") == 50000
    assert attributes.get("estilo") == "Sedán"
    assert attributes.get("puertas") == 4
    assert attributes.get("provincia") == "San José"

def test_extract_car_data(mock_html_content):
    scraper = CRAutosScraper(headless=True, max_pages=1)
    soup = BeautifulSoup(mock_html_content, 'html.parser')
    inventory_elements = soup.find_all('div', class_='inventory')

    # Check the first car
    car_data_1 = scraper._extract_car_data(inventory_elements[0])

    assert car_data_1 is not None
    assert car_data_1["titulo_completo"] == "Toyota Corolla 2018"
    assert car_data_1["marca"] == "Toyota"
    assert car_data_1["modelo"] == "Corolla"
    assert car_data_1["año"] == "2018"
    assert car_data_1["car_id"] == "123456"
    assert car_data_1["precio"] == "¢ 8,500,000"
    assert car_data_1["precio_numerico"] == 8500000.0
    assert car_data_1["url_imagen"] == "http://example.com/image.jpg"
    assert car_data_1["vendedor"] == "Agencia de Autos S.A."
    assert car_data_1["telefono"] == "8888-8888"

    # Check the second car
    car_data_2 = scraper._extract_car_data(inventory_elements[1])

    assert car_data_2 is not None
    assert car_data_2["titulo_completo"] == "Honda Civic 2020"
    assert car_data_2["marca"] == "Honda"
    assert car_data_2["car_id"] == "654321"
    assert car_data_2["transmision"] == "Manual"
    assert car_data_2["vendedor"] == "Juan Pérez"


@patch('backend.scrapers.crautos_scraper.webdriver.Chrome')
@patch('backend.scrapers.crautos_scraper.WebDriverWait')
def test_scrape_page(mock_wait, mock_chrome, mock_html_content):
    # Setup mock driver
    mock_driver_instance = MagicMock()
    mock_driver_instance.page_source = mock_html_content
    mock_chrome.return_value = mock_driver_instance

    # We want WebDriverWait to just return and not actually wait
    mock_wait_instance = MagicMock()
    mock_wait.return_value = mock_wait_instance

    scraper = CRAutosScraper(headless=True, max_pages=1)
    scraper.driver = mock_driver_instance

    # Perform _scrape_page
    cars = scraper._scrape_page(1)

    assert len(cars) == 2
    assert cars[0]["marca"] == "Toyota"
    assert cars[1]["marca"] == "Honda"

    # Verify driver interactions
    mock_driver_instance.get.assert_called_once()
    assert "p=1" in mock_driver_instance.get.call_args[0][0]

@patch('backend.scrapers.crautos_scraper.CRAutosScraper._scrape_page')
def test_scrape_all_cars(mock_scrape_page):
    # Mocking the _scrape_page method to return a dummy list of cars on the first call, and empty on the second
    mock_scrape_page.side_effect = [
        [{"marca": "Toyota", "modelo": "Yaris"}],
        [] # Empty list to simulate no more pages
    ]

    # Use max_pages=5, but it should stop early due to the empty list logic in scrape_all_cars
    scraper = CRAutosScraper(headless=True, max_pages=5)

    # Mock the driver setup and close so it doesn't open an actual browser
    scraper.setup_driver = MagicMock()
    scraper.close_driver = MagicMock()

    # To speed up the test and not wait on sleep
    with patch('time.sleep', return_value=None):
        results = scraper.scrape_all_cars()

    assert len(results) == 1
    assert results[0]["marca"] == "Toyota"

    # Check that setup and teardown were called
    scraper.setup_driver.assert_called_once()
    scraper.close_driver.assert_called_once()

    # _scrape_page should be called twice (1 for the result, 1 for the empty stop)
    assert mock_scrape_page.call_count == 2
