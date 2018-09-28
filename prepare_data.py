import csv
import os
import zipfile
from collections import OrderedDict
from typing import Tuple, List, Dict

import geopy.distance
import requests
import structlog

log = structlog.get_logger()
Point = Tuple[float, float]

COUNTRY_CODE = 'LV'
CITIES_DATA = f'{COUNTRY_CODE}.csv'
CITIES_DISTANCE = f'{COUNTRY_CODE}_DISTANCE.csv'
IS_SIMPLE = True


class Downloader:
    CITIES_TYPES = {'PPLA', 'PPLC'}  # city and capital
    CITY_NAME = 2
    LAT = 4
    long = 5
    OBJECT_TYPE = 7

    @property
    def zip_filename(self) -> str:
        return f'{COUNTRY_CODE}.zip'

    @property
    def raw_cities_data(self) -> str:
        return f'{COUNTRY_CODE}.txt'

    @property
    def url(self) -> str:
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

                fieldnames = ['name', 'lat', 'long']
                writer = csv.DictWriter(csv_file_w, fieldnames=fieldnames)
                writer.writeheader()

                reader = csv.reader(csv_file_r, delimiter='\t')
                for row in filter(lambda x: x[self.OBJECT_TYPE] in self.CITIES_TYPES, reader):
                    data = {
                        'name': row[self.CITY_NAME],
                        'lat': row[self.LAT],
                        'long': row[self.long],
                    }
                    log.msg(f'Write row to file {CITIES_DATA}', **data)
                    writer.writerow(data)

        log.msg(f'Remove temp raw data: {self.raw_cities_data}')
        os.remove(self.raw_cities_data)

    def download(self):
        self.download_cities_information()
        self.prepare_csv()


class DistanceMatrix:
    cities: List[OrderedDict] = []
    matrix: List[Dict] = []
    is_simple: bool = IS_SIMPLE
    source: str = CITIES_DATA
    counter = 0

    @staticmethod
    def calculate(point1: Point, point2: Point, util='m') -> float:
        return round(getattr(geopy.distance.vincenty(point1, point2), util), 2)

    def init_cities(self):
        with open(CITIES_DATA, newline='') as csv_file_r:
            reader = csv.DictReader(csv_file_r)
            self.cities = [row for row in reader]

    def get_point(self, city) -> Point:
        return city['lat'], city['long']

    def init_matrix(self):
        if self.cities:
            with open(CITIES_DISTANCE, 'w', newline='') as csv_file_w:
                fieldnames = ['name'] + [city['name'] for city in self.cities]
                writer = csv.DictWriter(csv_file_w, fieldnames=fieldnames)
                writer.writeheader()

                for city_y in self.cities:
                    data = {'name': city_y['name']}
                    for city_x in self.cities:
                        data.update({
                            city_x['name']: self.calculate(
                                self.get_point(city_y),
                                self.get_point(city_x)
                            )
                        })

                    log.msg(f'Write row to file {CITIES_DISTANCE}', **data)
                    writer.writerow(data)


if __name__ == '__main__':
    Downloader().download()
    dm = DistanceMatrix()
    dm.init_cities()
    dm.init_matrix()

