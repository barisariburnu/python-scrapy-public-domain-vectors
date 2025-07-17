# -*- coding: utf-8 -*-

import logging
from scrapy.exceptions import DropItem
from publicdomainvectors.settings import MONGO_USERNAME, MONGO_PASSWORD, MONGO_DATABASE
from pymongo import MongoClient

client = MongoClient(
    f"mongodb+srv://{MONGO_USERNAME}:{MONGO_PASSWORD}@cluster.u8tllb7.mongodb.net/{MONGO_DATABASE}"
    f"?retryWrites=true&w=majority", tls=True, tlsAllowInvalidCertificates=True
)
db = client.get_default_database()
logger = logging.getLogger(__name__)


class PublicdomainvectorsPipeline(object):
    def __init__(self):
        self.post_seen = set()

    def process_item(self, item, spider):
        if item['source_url'] in self.post_seen:
            raise DropItem(f"Duplicate item found: {item['source_url']}")

        if 'download_url' not in item:
            raise DropItem(f"Exception: {item['source_url']}")

        try:
            if str(db.vectors.insert_one(item)):
                logger.info('Successful vector id: {0}'.format(item['filename']))
                self.post_seen.add(item['source_url'])
            else:
                logger.error('Error vector id: {0}'.format(item['filename']))
                raise DropItem(f"Error item: {item['filename']}")
        except Exception as ex:
            raise DropItem(ex)

        return item
