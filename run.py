from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from scraper.crawler import MorganLewisCrawler

scrapy_settings = Settings()
scrapy_settings.setmodule('configures.settings')

runner = CrawlerProcess(scrapy_settings)
runner.crawl(MorganLewisCrawler)
runner.start()
