from publicdomainvectors.items import PublicdomainvectorsItemParser
from publicdomainvectors.settings import CATEGORIES
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class PublicDomainVectorsSpider(CrawlSpider):
    name = 'publicdomainvectors'
    allowed_domains = ['publicdomainvectors.org']
    start_urls = [f'https://publicdomainvectors.org/en/free-clipart/{CATEGORIES[0]}/date/all/360/1']

    rules = (
        Rule(LinkExtractor(restrict_css='.vector-thumbnail-wrap > a'), callback='parse_item', follow=False),
        Rule(LinkExtractor(restrict_css='.next > a'), follow=True),
    )

    def parse_item(self, response):
        item = PublicdomainvectorsItemParser(response)

        if not item.save():
            return {
                'source_url': response.url
            }

        return item.to_json()
