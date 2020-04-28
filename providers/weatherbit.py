# Uses Weatherbit.io API: https://www.weatherbit.io/
from acquire import Acquire

import json
import logging
import requests
from collections import namedtuple


WeatherbitTuple = namedtuple('Weather', ['provider', 'temp', 'temp_min', 'temp_max', 'icon', 'summary', 'forecast_summary', 'nearest_storm_distance', 'alert_title', 'alert_description'])


class Weatherbit(Acquire):


    DEFAULT = WeatherbitTuple(provider='Weatherbit.io', temp=-99, temp_min=-99, temp_max=-99, icon='n/a', summary='n/a',
                              forecast_summary='n/a', nearest_storm_distance=None, alert_title=None, alert_description=None)


    def __init__(self, key, lat, lon, units, cache_ttl):
        self.key = key
        self.lat = lat
        self.lon = lon
        self.units = units
        self.cache_ttl = cache_ttl


    def cache_name(self):
        return "weatherbit.json"


    def ttl(self):
        return self.cache_ttl


    def acquire(self):
        logging.info("Getting a fresh forecast from the internet using Weatherbit.io...")

        try:
            r = requests.get(
                "https://api.weatherbit.io/v2.0/current",
                params = {
                    "key" : self.key,
                    "lat" : self.lat,
                    "lon" : self.lon,
                    "units" : self.units
                }
            )
            current = r.json()

            r = requests.get(
                "https://api.weatherbit.io/v2.0/forecast/daily",
                params = {
                    "key" : self.key,
                    "lat" : self.lat,
                    "lon" : self.lon,
                    "units" : self.units
                }
            )
            forecast = r.json()

            result = {
                'current'  : current,
                'forecast' : forecast
            }
            # TODO dirty hack to merge two requests as one (+ using the status code from the last one)
            return r.status_code, json.dumps(result)

        except Exception as e:
            logging.exception(e)

        return (None, None)


    def get(self):
        try:
            forecast_data = self.load()
            if forecast_data is None:
                return self.DEFAULT
        
            c = forecast_data['current']['data'][0]
            d = forecast_data['forecast']['data'][0]
            
            return WeatherbitTuple(
                provider='Weatherbit.io',
                temp=c['temp'],
                temp_min=d['low_temp'],
                temp_max=d['max_temp'],
                icon=c['weather']['icon'] if 'weather' in c else None,
                summary=c['weather']['description'] if 'weather' in c else None,
                forecast_summary=d['weather']['description'] if 'weather' in d else None,
                nearest_storm_distance=None,    # Unsupported by this provider yet
                alert_title=None,               # Unsupported by this provider yet
                alert_description=None          # Unsupported by this provider yet
            )

        except Exception as e:
            logging.exception(e)
            return self.DEFAULT

