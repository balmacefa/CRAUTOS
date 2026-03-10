import asyncio
import json
import re
import os
import time
import logging
import random
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from backend.config.settings import settings
from backend.utils.logger import logger

# Import MARCAS from external repo code if needed or define a basic one
MARCAS = [
    "ACURA", "ALFA ROMEO", "AMC", "ARO", "ASIA", "ASTON MARTIN", "AUDI", "AUSTIN", "BAW", "BENTLEY", "BLUEBIRD", "BMW", "BRILLIANCE", "BUICK", "BYD", "CADILLAC", "CHANA", "CHANGAN", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DACIA", "DAEWOO", "DAIHATSU", "DATSUN", "DODGE/RAM", "DODGE", "RAM", "DONFENG(ZNA)", "DONFENG", "ZNA", "EAGLE", "FAW", "FERRARI", "FIAT", "FORD", "FOTON", "FREIGHTLINER", "GEELY", "GENESIS", "GEO", "GMC", "GONOW", "GREAT WALL", "HAFEI", "HAIMA", "HEIBAO", "HIGER", "HINO", "HONDA", "HUMMER", "HYUNDAI", "INFINITI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC", "JAGUAR", "JEEP", "JINBEI", "JMC", "JONWAY", "KENWORTH", "KIA", "LADA", "LAMBORGHINI", "LANCIA", "LAND ROVER", "LEXUS", "LIFAN", "LINCOLN", "LOTUS", "MACK", "MAHINDRA", "MASERATI", "MAZDA", "MCLAREN", "MERCEDES BENZ", "MERCURY", "MG", "MINI", "MITSUBISHI", "MORGAN", "NISSAN", "OLDSMOBILE", "OPEL", "PETERBILT", "PEUGEOT", "PLYMOUTH", "POLARIS", "PONTIAC", "PORSCHE", "PROTON", "PUMA", "RAM", "RENAULT", "ROVER", "SAAB", "SAMSUNG", "SATURN", "SCION", "SEAT", "SKODA", "SMART", "SOUEAST", "SSANG YONG", "SUBARU", "SUZUKI", "TATA", "TIANMA", "TOYOTA", "TRIUMPH", "UAZ", "VOLKSWAGEN", "VOLVO", "WESTERN STAR", "WILLYS", "YUEJIN", "YUGO", "ZNA", "ZOTYE", "ZX AUTO"
]

class CRAutosScraper:
    def __init__(self, headless: bool = None, max_pages: int = None):
        self.headless = headless if headless is not None else settings.SCRAPER_HEADLESS
        # Force max_pages for tests if passed
        self.max_pages = max_pages if max_pages is not None else settings.SCRAPER_MAX_PAGES
        self.base_url = settings.CRAUTOS_USED_CARS_URL
        self.cars_data = []

    def scrape_all_cars(self) -> List[Dict]:
        """Synchronous wrapper to scrape all cars to maintain compatibility with existing codebase"""
        try:
            return asyncio.run(self._async_scrape_all_cars())
        except RuntimeError:
            # If an event loop is already running (e.g., inside FastAPI task)
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(self._async_scrape_all_cars())

    async def _async_scrape_all_cars(self) -> List[Dict]:
        logger.info("Starting asynchronous scraping with Playwright...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # Step 1: Get URLs
            car_urls = await self._get_car_urls(page)
            logger.info(f"Found {len(car_urls)} car URLs to scrape.")
            
            # Step 2: Scrape details
            # We will process them sequentially or with bounded concurrency to not overwhelm
            semaphore = asyncio.Semaphore(10) # 10 concurrent requests
            
            tasks = [self._scrape_car_details_task(url, context, semaphore) for url in car_urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for res in results:
                if isinstance(res, dict) and res:
                    self.cars_data.append(res)
                elif isinstance(res, Exception):
                    logger.error(f"Error scraping a URL: {res}")

            await browser.close()
            
        logger.info(f"Scraping completed. Total cars: {len(self.cars_data)}")
        return self.cars_data

    async def _get_car_urls(self, page) -> List[str]:
        detail_urls = set()

        try:
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=60000)
            
            # Click search to list all cars
            try:
                await page.locator(".btn.btn-lg.btn-success").click(timeout=10000)
            except Exception:
                logger.warning("Could not find or click the search button, continuing anyway...")

            # Determine total pages
            last_page_number = 1
            try:
                last_page_link = page.locator('a:has-text("Última Página")')
                if await last_page_link.count() > 0:
                    href = await last_page_link.first.get_attribute("href", timeout=5000)
                    if href:
                        match = re.search(r"p\('(\d+)'\)", href)
                        if match:
                            last_page_number = int(match.group(1))
            except Exception as e:
                logger.error(f"Error finding last page: {e}")
            
            # Use self.max_pages if set to limit
            pages_to_scrape = min(last_page_number, self.max_pages)
            logger.info(f"Will scrape {pages_to_scrape} pages (out of {last_page_number} total).")
            
            for page_num in range(1, pages_to_scrape + 1):
                logger.info(f"Extracting URLs from page {page_num}/{pages_to_scrape}...")

                if page_num > 1:
                    try:
                        async with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                            await page.evaluate(f"p('{page_num}')")
                    except Exception as e:
                        logger.error(f"Failed to navigate to page {page_num}: {e}")
                        continue

                try:
                    await page.wait_for_selector('a[href^="cardetail.cfm"]', timeout=10000)
                    links = await page.locator('a[href^="cardetail.cfm"]').all()

                    for link in links:
                        href = await link.get_attribute("href")
                        if href:
                            absolute_url = urljoin(page.url, href)
                            detail_urls.add(absolute_url)
                except Exception as e:
                    logger.warning(f"No detail links found on page {page_num}: {e}")

        except Exception as e:
            logger.error(f"Error getting car URLs: {e}")

        return list(detail_urls)

    async def _scrape_car_details_task(self, url: str, context, semaphore: asyncio.Semaphore) -> Optional[Dict]:
        async with semaphore:
            page = None
            for attempt in range(3): # TRIES
                try:
                    page = await context.new_page()
                    # Block unnecessary resources for speed
                    await page.route(
                        "**/*",
                        lambda route: (
                            route.abort()
                            if route.request.resource_type in ["image", "stylesheet", "font", "media"]
                            else route.continue_()
                        ),
                    )

                    await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    data = await self._extract_car_data_playwright(page)
                    return data
                except Exception as e:
                    if attempt == 2:
                        logger.error(f"Failed to scrape {url} after 3 attempts: {e}")
                finally:
                    if page:
                        await page.close()
            return None

    async def _extract_car_data_playwright(self, page) -> Dict:
        data = {
            "fecha_extraccion": datetime.now().isoformat(),
            "url_detalle": page.url,
            "es_financiado": False,
            "recibe_vehiculo": False,
        }
        
        # Extract ID
        try:
            parsed = parse_qs(urlparse(page.url).query)
            if "c" in parsed:
                data["car_id"] = parsed["c"][0]
            elif "id" in parsed:
                data["car_id"] = parsed["id"][0]
        except Exception:
            pass

        # Parse title
        try:
            title_element = page.locator("div.header-text h1").first
            full_title_text = (await title_element.inner_text()).strip()
            data["titulo_completo"] = full_title_text

            title_parts = full_title_text.split()
            if title_parts and title_parts[-1].isdigit() and len(title_parts[-1]) == 4:
                data["año"] = title_parts.pop()

            remaining_title = " ".join(title_parts)
            for marca in MARCAS:
                if remaining_title.upper().startswith(marca):
                    data["marca"] = marca
                    data["modelo"] = remaining_title[len(marca):].strip()
                    break
            if "modelo" not in data:
                data["modelo"] = remaining_title
        except Exception:
            pass

        # Parse price
        try:
            price_crc_text = await page.locator("div.header-text h3").first.inner_text()
            data["precio"] = price_crc_text
            cleaned = re.sub(r'[^\d]', '', price_crc_text)
            if cleaned:
                data["precio_numerico"] = float(cleaned)
        except Exception:
            try:
                # alternative price locator
                price_usd_text = await page.locator("div.header-text h1").nth(1).inner_text()
                data["precio"] = price_usd_text
                cleaned = re.sub(r'[^\d.]', '', price_usd_text)
                if cleaned:
                    data["precio_numerico"] = float(cleaned)
            except Exception:
                pass

        # Extract image
        try:
            data["url_imagen"] = await page.locator("div.bannerimg").get_attribute("data-image-src", timeout=2000)
        except Exception:
            pass

        # Extract general info (from tables)
        try:
            for row in await page.locator("table.mytext2 tbody tr").all():
                cells = await row.locator("td").all()
                if len(cells) == 2:
                    key = (await cells[0].inner_text()).strip().lower()
                    value = (await cells[1].inner_text()).strip()

                    if "transmisión" in key or "transmision" in key:
                        data["transmision"] = value
                    elif "combustible" in key:
                        data["combustible"] = value
                    elif "kilometraje" in key:
                        data["kilometraje"] = value
                        km_val = re.sub(r'[^\d]', '', value)
                        if km_val:
                            data["kilometraje_numerico"] = int(km_val)
                    elif "estilo" in key:
                        data["estilo"] = value
                    elif "provincia" in key:
                        data["provincia"] = value
        except Exception:
            pass
            
        # Optional: Vendor info
        try:
            seller_table = page.locator('//table[.//td[contains(., "Vendedor")]]')
            if await seller_table.count() > 0:
                for row in await seller_table.locator("tr").all():
                    cells = await row.locator("td").all()
                    if len(cells) == 2:
                        key = (await cells[0].inner_text()).strip().lower().replace(":", "")
                        value = (await cells[1].inner_text()).strip()
                        if "vendedor" in key or "nombre" in key:
                            data["vendedor"] = value
        except Exception:
            pass

        # Optional: Financing
        try:
            fin_text = await page.content()
            if "Financiado" in fin_text:
                data["es_financiado"] = True
            if "Recibe" in fin_text:
                data["recibe_vehiculo"] = True
        except Exception:
            pass

        return data
