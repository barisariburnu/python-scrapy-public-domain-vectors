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

DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


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
        return os.path.exists(eps) or os.path.exists(svg)

    def __make_dirs(self, path, filename):
        fpath = os.path.join(path, filename)
        if not os.path.isdir(fpath):
            os.makedirs(fpath)

    def __download(self, path, filename, extension):
        fname = os.path.join(path, filename, f'{filename}.{extension}')
        r = requests.get(self.download_url)
        if r.status_code != 200:
            raise Exception(f"Download failed with status {r.status_code}")
        with open(fname, 'wb') as f:
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
            reg = re.compile(r'(\.\d)(pt)')  # regex to search numbers with "pt"
            svg = sv1.to_str().decode('utf-8', errors='ignore')  # svgutils delivers ascii byte strings.
            svg = reg.sub(r'\1', svg)  # the incorrectly added "pt" unit is removed here
    
            scour_options = scour.sanitizeOptions(options=None)  # get a clean scour options object
            scour_options.remove_metadata = True  # change any option you like
            try:
                clean_svg_str = scour.scourString(svg, options=scour_options)  # use scour
            except Exception as scour_ex:
                print(f'Scour failed for {filename}: {scour_ex}. Skipping scour.')
                clean_svg_str = svg
            with open(fname, "w") as f:
                f.write(clean_svg_str)
        except Exception as ex:
            print(f'Clean SVG exception for {filename}: {ex}')

    def save(self):
        path = self.path
        filename = self.filename
        extension = self.extension

        try:
            if self.__is_exists(path=path, filename=filename):
                print(f'{self.response.url} is already downloaded.')
                return True

            self.__make_dirs(path=path, filename=filename)
            self.__download(path=path, filename=filename, extension=extension)

            if extension == 'zip':
                try:
                    self.__unzip(path=path, filename=filename)
                except zipfile.BadZipFile:
                    print(f'File {filename}.zip is not a valid zip, treating as SVG.')
                    fake_zip = os.path.join(path, filename, f'{filename}.zip')
                    temp_svg = os.path.join(path, filename, f'{filename}.svg')
                    os.rename(fake_zip, temp_svg)

            self.__copy_files(path=path, filename=filename)
            return True
        except Exception as ex:
            print(f'Save exception for {filename}: {ex}')
            if os.path.exists(os.path.join(path, filename)):
                shutil.rmtree(os.path.join(path, filename))
            return False

    def to_json(self):
        return {
            'source_url': self.source_url,
            'filename': self.filename,
            'category': self.category,
            'download_url': self.download_url
        }


def process_existing_zips(data_path=DATA_PATH):
    print(f'Starting to walk directory: {data_path}')
    
    def clean_svg(path, filename):
        fname = os.path.join(path, f'{filename}.svg')
        if not os.path.exists(fname):
            return
        try:
            sv1 = svgutils.transform.fromfile(fname)
            reg = re.compile(r'(\.\d)(pt)')
            svg = sv1.to_str().decode()
            svg = reg.sub(r'\1', svg)
            scour_options = scour.sanitizeOptions(options=None)
            scour_options.remove_metadata = True
            try:
                clean_svg_str = scour.scourString(svg, options=scour_options)
            except Exception as scour_ex:
                print(f'Scour failed for {filename}: {scour_ex}. Skipping scour.')
                clean_svg_str = svg
            with open(fname, "w") as f:
                f.write(clean_svg_str)
        except Exception as ex:
            print(f'Clean SVG exception for {filename}: {ex}')

    for root, dirs, files in os.walk(data_path):
        print(f'Checking directory: {root}')
        rel_path = os.path.relpath(root, data_path)
        depth = len(rel_path.split(os.sep))
        if depth == 1:
            continue
        zip_files = [f for f in files if f.endswith('.zip')]
        if not zip_files:
            print(f'No zip files in {root}')
            for f in files:
                ext = os.path.splitext(f)[1][1:]
                if ext in ['svg', 'eps']:
                    src = os.path.join(root, f)
                    filename = os.path.splitext(f)[0]
                    parent = os.path.dirname(root)
                    dst = os.path.join(parent, f'{filename}.{ext}')
                    if os.path.exists(dst):
                        print(f'{filename} already exists in parent. Removing duplicate from subfolder.')
                        os.remove(src)
                        continue
                    shutil.move(src, dst)
                    if ext == 'svg':
                        clean_svg(parent, filename)
                    print(f'Moved {f} to parent')
            if not os.listdir(root):
                shutil.rmtree(root)
                print(f'Deleted empty directory {root}')
        for file in zip_files:
            if file.endswith('.zip'):
                zip_path = os.path.join(root, file)
                filename = os.path.splitext(file)[0]
                parent = os.path.dirname(root)
                svg_path = os.path.join(parent, f'{filename}.svg')
                if os.path.exists(svg_path):
                    print(f'{filename} already processed.')
                    continue
                temp_dir = os.path.join(root, f'temp_{filename}')
                os.makedirs(temp_dir, exist_ok=True)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as z:
                        z.extractall(temp_dir)
                    for f in os.listdir(temp_dir):
                        ext = os.path.splitext(f)[1][1:]
                        if ext in ["eps", "svg"]:
                            src = os.path.join(temp_dir, f)
                            dst = os.path.join(parent, f'{filename}.{ext}')
                            shutil.copyfile(src, dst)
                    eps = os.path.join(parent, f'{filename}.eps')
                    svg = os.path.join(parent, f'{filename}.svg')
                    if os.path.exists(eps) and os.path.exists(svg):
                        os.remove(eps)
                    if os.path.exists(svg):
                        clean_svg(parent, filename)
                    shutil.rmtree(temp_dir)
                    os.remove(zip_path)
                    shutil.rmtree(root)
                    print(f'Processed {filename}')
                except zipfile.BadZipFile:
                    print(f'File {filename}.zip is not a valid zip, treating as SVG.')
                    fake_zip = zip_path
                    temp_svg = os.path.join(root, f'{filename}.svg')
                    os.rename(fake_zip, temp_svg)
                    dst_svg = os.path.join(parent, f'{filename}.svg')
                    shutil.copyfile(temp_svg, dst_svg)
                    clean_svg(parent, filename)
                    shutil.rmtree(root)
                    print(f'Processed invalid zip {filename} as SVG')
                except Exception as ex:
                    print(f'Error processing {filename}: {ex}')
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)
                    # Do not remove root here to avoid data loss