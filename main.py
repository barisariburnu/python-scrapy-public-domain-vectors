import sys
from publicdomainvectors.items import process_existing_zips
from scrapy import cmdline

if len(sys.argv) > 1 and sys.argv[1] == 'unzip':
    process_existing_zips()
else:
    cmdline.execute("scrapy crawl publicdomainvectors".split())