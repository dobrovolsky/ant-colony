import os
import zipfile
import csv

import requests
import structlog

log = structlog.get_logger()

COUNTRY_CODE = 'LV'
CITIES_DATA = f'{COUNTRY_CODE}.csv'


class Downloader:
    CITIES_TYPES = {'PPLA', 'PPLC'}  # city and capital
    CITY_NAME = 2
    LAT = 4
    LON = 5
    OBJECT_TYPE = 7

    @property
    def zip_filename(self):
        return f'{COUNTRY_CODE}.zip'

    @property
    def raw_cities_data(self):
        return f'{COUNTRY_CODE}.txt'

    @property
    def url(self):
        return f'http://download.geonames.org/export/dump/{self.zip_filename}'

    def download_cities_information(self):
        log.msg(f'start downloading cities information for {COUNTRY_CODE}')
        r = requests.get(self.url, stream=True)
        with open(self.zip_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        log.msg('Done')

        log.msg(f'Extracting data to file {self.raw_cities_data}')
        with zipfile.ZipFile(self.zip_filename, 'r') as z:
            z.extract(self.raw_cities_data)

        log.msg('Remove temp zip')
        os.remove(self.zip_filename)

    def prepare_csv(self):
        with open(self.raw_cities_data, newline='') as csv_file_r:
            with open(CITIES_DATA, 'w', newline='') as csv_file_w:

                fieldnames = ['name', 'lat', 'lon']
                writer = csv.DictWriter(csv_file_w, fieldnames=fieldnames)
                writer.writeheader()

                reader = csv.reader(csv_file_r, delimiter='\t')
                for row in filter(lambda x: x[self.OBJECT_TYPE] in self.CITIES_TYPES, reader):
                    data = {
                        'name': row[self.CITY_NAME],
                        'lat': row[self.LAT],
                        'lon': row[self.LON],
                    }
                    log.msg(f'Write row to file {CITIES_DATA}', **data)
                    writer.writerow(data)

        log.msg(f'Remove temp raw data: {self.raw_cities_data}')
        os.remove(self.raw_cities_data)

    def download(self):
        self.download_cities_information()
        self.prepare_csv()


if __name__ == '__main__':
    Downloader().download()
