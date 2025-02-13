from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from news_scraper.spiders.news_scraper import NewsSpider
from news_scraper.spiders.financial_data_scraper import FinancialDataScraper

def main():
    company_name = input("Enter the company name: ")

    try:
        process = CrawlerProcess(get_project_settings())

        process.crawl(NewsSpider, company_name=company_name)
        process.crawl(FinancialDataScraper, company_name=company_name)

        process.start()

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
