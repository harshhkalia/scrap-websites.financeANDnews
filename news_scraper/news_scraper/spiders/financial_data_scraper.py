import scrapy
import json
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


class FinancialDataScraper(scrapy.Spider):
    name = "financial_data_scraper"

    company_to_ticker = {
        "infosys": "INFY:NSE", "wipro": "WIPRO:NSE", "google": "GOOG:NASDAQ",
        "microsoft": "MSFT:NASDAQ", "apple": "AAPL:NASDAQ", "amazon": "AMZN:NASDAQ",
        "tesla": "TSLA:NASDAQ", "facebook": "META:NASDAQ", "adobe": "ADBE:NASDAQ",
        "ibm": "IBM:NYSE", "nvidia": "NVDA:NASDAQ", "netflix": "NFLX:NASDAQ",
        "snap": "SNAP:NYSE", "twitter": "TWTR:NYSE", "intel": "INTC:NASDAQ",
        "spotify": "SPOT:NYSE", "salesforce": "CRM:NYSE", "paypal": "PYPL:NASDAQ",
        "hcl": "HCLTECH:NSE", "shopify": "SHOP:NYSE",
    }

    def __init__(self, company_name=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.company_name = company_name
        self.result_data = []
        self.driver = None

    def get_driver(self):
        """Set up Selenium WebDriver."""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors=yes")
        chrome_options.add_argument("--headless")
        driver_path = ChromeDriverManager().install()
        service = Service(driver_path)
        print("started scrapping the data...")
        return webdriver.Chrome(service=service, options=chrome_options)

    def start_requests(self):
        """Start the scraping process."""
        if not self.company_name:
            self.logger.error("No company name provided!")
            return []

        company_name_lower = self.company_name.lower()
        ticker_symbol = self.company_to_ticker.get(company_name_lower)

        if not ticker_symbol:
            self.logger.error(f"No ticker symbol found for company name: {self.company_name}")
            return []

        self.logger.info(f"Using ticker symbol: {ticker_symbol}")

        yahoo_ticker = ticker_symbol.split(':')[0]
        google_ticker = ticker_symbol

        self.driver = self.get_driver()
        self.scrape_yahoo_finance(yahoo_ticker)
        self.scrape_google_finance(google_ticker)
        self.save_to_json()

    def scrape_yahoo_finance(self, ticker_symbol):
        """Scrape Yahoo Finance using Selenium."""
        url = f"https://finance.yahoo.com/quote/{ticker_symbol}/"
        self.logger.info(f"Loading Yahoo Finance URL: {url}")

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'fin-streamer[data-field="regularMarketPrice"]'))
            )
            print("loaded first page to scrape the data")
        except Exception as e:
            self.logger.error(f"Failed to load Yahoo Finance page: {e}")
            return

        response = scrapy.http.HtmlResponse(
            url=self.driver.current_url,
            body=self.driver.page_source,
            encoding='utf-8',
        )
        self.extract_financial_data_from_yahoo(response)

    def scrape_google_finance(self, ticker_symbol):
        """Scrape Google Finance using Selenium."""
        url = f"https://www.google.com/finance/quote/{ticker_symbol}?hl=en"
        self.logger.info(f"Loading Google Finance URL: {url}")

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.gyFHrc > div.P6K39c'))
            )
            print("loaded second page to scrape the data")
        except Exception as e:
            self.logger.error(f"Failed to load Google Finance page: {e}")
            return

        response = scrapy.http.HtmlResponse(
            url=self.driver.current_url,
            body=self.driver.page_source,
            encoding='utf-8',
        )
        self.extract_financial_data_from_google(response)

    def extract_financial_data_from_yahoo(self, response):
        """Extract financial data from Yahoo Finance."""
        try:
            soup = BeautifulSoup(response.body, 'html.parser')
            financial_data = {'source': 'Yahoo Finance'}

            selectors = {
                'stock_price': 'fin-streamer[data-field="regularMarketPrice"]',
                'market_cap': 'fin-streamer[data-field="marketCap"]',
                'pe_ratio': 'fin-streamer[data-field="trailingPE"]',
                '52_week_range': 'fin-streamer[data-field="fiftyTwoWeekRange"]',
                'dividend_yield': 'span:contains("Forward Dividend & Yield") + span',
                'earnings_date': 'span:contains("Earnings Date") + span',
                'ex_dividend_date': 'span:contains("Ex-Dividend Date") + span',
                '1y_target_est': 'fin-streamer[data-field="targetMeanPrice"]',
                'avg_volume': 'fin-streamer[data-field="averageVolume"]'
            }

            for key, selector in selectors.items():
                element = soup.select_one(selector)
                financial_data[key] = element.text.strip() if element else "No data found" 

            print("extracted data from yahoo finance")
            self.result_data.append(financial_data)
        except Exception as e:
            self.logger.error(f"Error extracting Yahoo Finance data: {e}")

    def extract_financial_data_from_google(self, response):
        """Extract financial data from Google Finance."""
        try:
            soup = BeautifulSoup(response.body, 'html.parser')
            financial_data = {'source': 'Google Finance'}

            stock_price = soup.select_one('div[jsname="ip75Cb"] > div.YMlKec.fxKbKc')
            if stock_price:
                financial_data['stock_price'] = stock_price.text.strip()

            financial_rows = soup.select('div.gyFHrc')

            for row in financial_rows:
                label_div = row.select_one('div.mfs7Fc')
                value_div = row.select_one('div.P6K39c')

                if label_div and value_div:
                    label = label_div.text.strip()
                    value = value_div.text.strip()

                    label_map = {
                        "Market cap": "market_cap", "Avg Volume": "avg_volume",
                        "P/E ratio": "pe_ratio", "Dividend yield": "dividend_yield",
                        "Primary exchange": "primary_exchange", "Previous close": "previous_close",
                        "Day range": "day_range", "Year range": "year_range"
                    }

                    if label in label_map:
                        financial_data[label_map[label]] = value

            print("extracted data from google finance")
            self.result_data.append(financial_data)
        except Exception as e:
            self.logger.error(f"Error extracting Google Finance data: {e}")

    def save_to_json(self):
        """Save extracted data to a JSON file."""
        try:
            data_folder = os.path.join(os.getcwd(), "financial-data")
            os.makedirs(data_folder, exist_ok=True)
            filename = os.path.join(data_folder, f"{self.company_name}_data.json")
            with open(filename, "w") as f:
                json.dump(self.result_data, f, indent=4)
            self.logger.info(f"Results successfully saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error while saving JSON file: {e}")

    def closed(self, reason):
        """Clean up resources when spider closes."""
        if self.driver:
            self.driver.quit()
