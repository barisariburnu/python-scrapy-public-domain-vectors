# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import os
import re
import scrapy
import shutil
import zipfile
import requests
import svgutils
from scour import scour
from publicdomainvectors.settings import DATA_PATH


class PublicdomainvectorsItem(scrapy.Item):
    source_url = scrapy.Field()
    filename = scrapy.Field()
    category = scrapy.Field()
    download_url = scrapy.Field()


class PublicdomainvectorsItemParser(object):
    def __init__(self, response):
        self.base_url = 'https://publicdomainvectors.org'
        self.response = response

    @property
    def source_url(self):
        result = self.response.url
        return result

    @property
    def category(self):
        result = self.response.css('div.row:nth-child(2) > div.col-sm-12 > p > a::text').extract_first()
        return result

    @property
    def download_url(self):
        result = f'{self.base_url}{self.response.css("a.btn.btn-green.btn-lg::attr(href)").extract_first()}'
        return result

    @property
    def filename(self):
        result = self.response.url.split('/')[-1:][0].split('.')[0]
        return result

    @property
    def extension(self):
        result = self.download_url.split('.')[-1:][0]
        return result

    @property
    def path(self):
        result = os.path.join(DATA_PATH, self.category)
        return result

    def __is_exists(self, path, filename):
        eps = os.path.join(path, f'{filename}.eps')
        svg = os.path.join(path, f'{filename}.svg')
        return True if os.path.exists(eps) or os.path.exists(svg) else False

    def __make_dirs(self, path, filename):
        fpath = os.path.join(path, filename)
        if not os.path.isdir(fpath):
            os.makedirs(fpath)

    def __download(self, path, filename, extension):
        fname = os.path.join(path, filename, f'{filename}.{extension}')
        with open(fname, 'wb') as f:
            r = requests.get(self.download_url)
            f.write(r.content)

    def __unzip(self, path, filename):
        fname = os.path.join(path, filename, f'{filename}.zip')
        fpath = os.path.join(path, filename)

        with zipfile.ZipFile(fname, 'r') as z:
            z.extractall(fpath)

    def __copy_files(self, path, filename):
        fpath = os.path.join(path, filename)

        for f in os.listdir(fpath):
            ext = f.split('.')[-1:][0]
            if ext in ["eps", "svg"]:
                src = os.path.join(fpath, f)
                dst = os.path.join(path, f'{filename}.{ext}')
                shutil.copyfile(src, dst)

        eps = os.path.join(path, f'{filename}.eps')
        svg = os.path.join(path, f'{filename}.svg')
        if os.path.exists(eps) and os.path.exists(svg):
            os.remove(eps)

        if os.path.exists(svg):
            self.__clean_svg(path, filename)

        shutil.rmtree(fpath)

    def __clean_svg(self, path, filename):
        fname = os.path.join(path, f'{filename}.svg')

        if not os.path.exists(fname):
            return

        try:
            sv1 = svgutils.transform.fromfile(fname)
            reg = re.compile('(\.\d)(pt)')  # regex to search numbers with "pt"
            svg = sv1.to_str().decode()  # svgutils delivers ascii byte strings.
            svg = reg.sub(r'\1', svg)  # the incorrectly added "pt" unit is removed here

            scour_options = scour.sanitizeOptions(options=None)  # get a clean scour options object
            scour_options.remove_metadata = True  # change any option you like
            clean_svg = scour.scourString(svg, options=scour_options)  # use scour

            with open(fname, "w") as f:
                f.write(clean_svg)
        except Exception as ex:
            print(f'Exception: {ex}')
            raise ex

    def save(self):
        path = self.path
        filename = self.filename
        extension = self.extension

        try:
            if self.__is_exists(path=path, filename=filename):
                print(f'{self.response.url} is already download.')
                return

            self.__make_dirs(path=path, filename=filename)
            self.__download(path=path, filename=filename, extension=extension)

            if extension == 'zip':
                self.__unzip(path=path, filename=filename)

            self.__copy_files(path=path, filename=filename)
            return True
        except Exception as ex:
            print(f'Exception: {ex}')
            return False

    def to_json(self):
        return {
            'source_url': self.source_url,
            'filename': self.filename,
            'category': self.category,
            'download_url': self.download_url
        }
