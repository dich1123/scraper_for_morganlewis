import scrapy
from abc import ABCMeta, abstractmethod
from .parser import MorganLewisParser
from scrapy.utils.response import open_in_browser
import logging


class BaseCrawler(scrapy.spiders.Spider, metaclass=ABCMeta):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        parser_class = self._response_parser_class()
        self.response_parser = parser_class()

    @classmethod
    @abstractmethod
    def _response_parser_class(cls):
        raise NotImplementedError('Response parser class not setup')


class MorganLewisCrawler(BaseCrawler):
    custom_settings = {
        'ITEM_PIPELINES': {
            'pipelines.printing_pipeline.PrintingPipeline': 1,
        },
        'ROBOTSTXT_OBEY': False,
        'COOKIES_ENABLED': True,
        'COOKIES_DEBUG': False,
        'LOG_LEVEL': 'INFO',
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_DELAY': 0.25,
    }

    name = 'morgan_lewis_crawler'

    @classmethod
    def _response_parser_class(cls):
        return MorganLewisParser

    @classmethod
    def headers(cls) -> dict:
        return {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
        }

    @classmethod
    def domain(cls) -> str:
        return 'www.morganlewis.com'

    @classmethod
    def search_people_url(cls):
        people_search_amount = 1000000
        return f'https://{cls.domain()}/api/custom/peoplesearch/search?keyword=&category=' \
               f'bb82d24a9d7a45bd938533994c4e775a&sortBy=lastname&pageNum=1&' \
               f'numberPerPage={people_search_amount}&numberPerSection=5&enforceLanguage=&languageToEnforce=&' \
               f'school=&position=&location=&court=&judge=&isFacetRefresh=true'

    @classmethod
    def publications_url(cls) -> str:
        return f'https://{cls.domain()}/api/sitecore/accordion/getaccordionlist'

    @classmethod
    def form_data_publications(cls, item_id) -> dict:
        return {
            'itemID': f'{item_id}',
            'itemType': 'publicationitemlist',
            'printView': ''
        }

    def start_requests(self) -> scrapy.Request:
        yield scrapy.Request(
            url=self.search_people_url(),
            callback=self.parse_preview,
            dont_filter=True,
            headers=self.headers()
        )

    def parse_preview(self, response):
        preview_counter = 0
        for preview_record in self.response_parser.parse_preview_records(response, self.domain()):
            yield self.build_record_details_request(response, preview_record)
            preview_counter += 1
        logging.info(f'Parsed preview records: {preview_counter}')

    def build_record_details_request(self, response, preview_record):
        url = preview_record['profile_url']
        return scrapy.Request(
            url=url,
            callback=self.parse_record_details,
            dont_filter=True,
            headers=self.headers(),
            cb_kwargs={
                'preview_record': preview_record,
            }
        )

    def parse_record_details(self, response, preview_record):
        record_details = self.response_parser.parse_record_details(response)
        yield self.build_publications_request(response, preview_record, record_details)

    def build_publications_request(self, response, preview_record, record_details):
        item_id = record_details['item_id']
        return scrapy.FormRequest(
            url=self.publications_url(),
            formdata=self.form_data_publications(item_id),
            callback=self.create_item,
            dont_filter=True,
            headers=self.headers(),
            cb_kwargs={
                'preview_record': preview_record,
                'record_details': record_details,
            }
        )

    def create_item(self, response, preview_record, record_details):  # correct with needful fields
        item = self.response_parser.parse(response, preview_record, record_details)
        return item
