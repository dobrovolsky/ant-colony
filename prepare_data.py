import csv
import json
import os
import zipfile
from collections import OrderedDict
from typing import Tuple, List, Dict

import geopy.distance
import googlemaps
import requests
import structlog

import settings

Point = Tuple[float, float]

log = structlog.get_logger()

if not settings.IS_SIMPLE_DISTANCE:
    gmaps = googlemaps.Client(key=settings.API_KEY)


class Downloader:
    CITIES_TYPES = {'PPLA', 'PPLC'}  # city and capital
    CITY_NAME = 2
    LAT = 4
    LNG = 5
    OBJECT_TYPE = 7

    @property
    def zip_filename(self) -> str:
        return f'{settings.COUNTRY_CODE}.zip'

    @property
    def raw_cities_data(self) -> str:
        return f'{settings.COUNTRY_CODE}.txt'

    @property
    def url(self) -> str:
        return f'http://download.geonames.org/export/dump/{self.zip_filename}'

    def download_cities_information(self):
        log.info(f'start downloading cities information for {settings.COUNTRY_CODE}')
        r = requests.get(self.url, stream=True)
        with open(self.zip_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        log.info('Done')

        log.info(f'Extracting data to file {self.raw_cities_data}')
        with zipfile.ZipFile(self.zip_filename, 'r') as z:
            z.extract(self.raw_cities_data)

        log.info('Remove temp zip')
        os.remove(self.zip_filename)

    def prepare_csv(self, limit):
        with open(self.raw_cities_data, newline='') as csv_file_r:
            with open(settings.CITIES_DATA, 'w', newline='') as csv_file_w:
                fieldnames = ['name', 'lat', 'lng']
                writer = csv.DictWriter(csv_file_w, fieldnames=fieldnames)
                writer.writeheader()

                reader = csv.reader(csv_file_r, delimiter='\t')
                limit_counter = 0
                for row in filter(lambda x: x[self.OBJECT_TYPE] in self.CITIES_TYPES, reader):
                    data = {
                        'name': row[self.CITY_NAME],
                        'lat': row[self.LAT],
                        'lng': row[self.LNG],
                    }
                    log.info(f'Write row to file {settings.CITIES_DATA}', **data)
                    if limit and limit_counter > limit:
                        break
                    else:
                        limit_counter += 1
                    writer.writerow(data)

        log.info(f'Remove temp raw data: {self.raw_cities_data}')
        os.remove(self.raw_cities_data)

    def download(self, limit=settings.CITIES_LIMIT):
        self.download_cities_information()
        self.prepare_csv(limit)


class DistanceMatrix:
    cities: List[OrderedDict] = []
    matrix: List[Dict] = []
    source: str = settings.CITIES_DATA
    counter = 0

    cache = {}

    def calculate(self, point1: Point, point2: Point) -> float:
        cached_value = self.cache.get((point1, point2), None) or self.cache.get((point2, point1), None)

        if cached_value is not None:
            log.info(f'Cache hit for ', data=(point1, point2))
            return cached_value

        if settings.IS_SIMPLE_DISTANCE:
            distance = round(getattr(geopy.distance.vincenty(point1, point2), 'm'), 2)
        else:
            data = gmaps.distance_matrix(point1, point2)
            log.info(f'Received data from google', data=data)
            distance = data['rows'][0]['elements'][0]['distance']['value']

        log.info(f'Add to cache ', data=(point1, point2))
        self.cache[(point1, point2)] = distance
        return distance

    def init_cities(self):
        with open(settings.CITIES_DATA, newline='') as csv_file_r:
            reader = csv.DictReader(csv_file_r)
            self.cities = [row for row in reader]

    @staticmethod
    def get_point(city) -> Point:
        return float(city['lat']), float(city['lng'])

    def init_matrix(self):
        if self.cities:

            data = {}
            for city_y in self.cities:
                data[city_y['name']] = {
                    'point': self.get_point(city_y),
                    'cities': []
                }
                for city_x in self.cities:
                    data[city_y['name']]['cities'].append({
                        'name': city_x['name'],
                        'distance': self.calculate(self.get_point(city_y), self.get_point(city_x)),
                        'point': self.get_point(city_x)
                    })

            log.info(f'Write to file {settings.CITIES_DISTANCE}', **data)
            with open(settings.CITIES_DISTANCE, 'w') as json_f:
                json.dump(data, json_f, indent=4)


if __name__ == '__main__':
    Downloader().download()
    dm = DistanceMatrix()
    dm.init_cities()
    dm.init_matrix()
