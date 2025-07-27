from publicdomainvectors.items import PublicdomainvectorsItemParser
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
import scrapy
from publicdomainvectors.settings import MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE
from pymongo import MongoClient
import logging
logging.getLogger('pymongo').setLevel(logging.WARNING)

client = MongoClient(
    f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@cluster.u8tllb7.mongodb.net/{MONGO_DATABASE}"
    f"?retryWrites=true&w=majority", tls=True, tlsAllowInvalidCertificates=True
)
db = client.get_default_database()


class PublicDomainVectorsSpider(CrawlSpider):
    name = 'publicdomainvectors'
    allowed_domains = ['publicdomainvectors.org']
    rules = (
        Rule(LinkExtractor(restrict_css='.vector-thumbnail-wrap > a'), callback='parse_item', follow=False),
        Rule(LinkExtractor(restrict_css='.next > a'), follow=True),
    )

    def start_requests(self):
        for i in range(1, 2):
            yield scrapy.Request(
                url=f'https://publicdomainvectors.org/en/free-clipart/date/all/360/{i}'
            )
            

    def parse_item(self, response):
        item = PublicdomainvectorsItemParser(response)

        if db.vectors.find_one({"source_url": item.source_url}):
            print('Already exists vector: {0}'.format(item.filename))
            return

        if not item.save():
            print('Error occurred while downloading: {0}'.format(item.filename))
            return

        return item.to_json()
