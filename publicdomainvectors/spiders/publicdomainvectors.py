from publicdomainvectors.items import PublicdomainvectorsItemParser
from publicdomainvectors.settings import CATEGORIES
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from publicdomainvectors.settings import MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE
from pymongo import MongoClient

client = MongoClient(
    f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@ireland.xjelg.mongodb.net/{MONGO_DATABASE}"
    f"?retryWrites=true&w=majority", tls=True, tlsAllowInvalidCertificates=True
)
db = client.get_default_database()


class PublicDomainVectorsSpider(CrawlSpider):
    name = 'publicdomainvectors'
    allowed_domains = ['publicdomainvectors.org']
    start_urls = [f'https://publicdomainvectors.org/en/free-clipart/{CATEGORIES[4]}/date/all/360/1']

    rules = (
        Rule(LinkExtractor(restrict_css='.vector-thumbnail-wrap > a'), callback='parse_item', follow=False),
        Rule(LinkExtractor(restrict_css='.next > a'), follow=True),
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
