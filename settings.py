import os

import structlog
from envparse import env

log = structlog.get_logger()

env_file_path = os.path.join(os.path.dirname(__file__), '.env')
env.read_envfile(env_file_path)

IS_SIMPLE_DISTANCE = env.bool('IS_SIMPLE_DISTANCE', default=True)
COUNTRY_CODE = env.str('COUNTRY_CODE')

CITIES_DATA = f'{COUNTRY_CODE}.csv'
CITIES_DISTANCE = f'{COUNTRY_CODE}_DISTANCE.json'
CITIES_LIMIT = 24


if not IS_SIMPLE_DISTANCE:
    API_KEY = env.str('API_KEY')
else:
    API_KEY = ''

log.debug('Load settings', IS_SIMPLE_DISTANCE=IS_SIMPLE_DISTANCE, COUNTRY_CODE=COUNTRY_CODE, API_KEY=API_KEY,
          CITIES_DATA=CITIES_DATA, CITIES_DISTANCE=CITIES_DISTANCE)
