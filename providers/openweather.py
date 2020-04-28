# Uses OpenWeather's One Call API: https://openweathermap.org/api/one-call-api - a result of DarkSky acquisition by Apple
from acquire import Acquire

import logging
import requests
from collections import namedtuple


OpenWeatherTuple = namedtuple('Weather', ['temp', 'temp_min', 'temp_max', 'icon', 'summary', 'forecast_summary', 'nearest_storm_distance', 'alert_title', 'alert_description'])


class OpenWeather(Acquire):


    DEFAULT = OpenWeatherTuple(temp=-99, temp_min=-99, temp_max=-99, icon='n/a', summary='n/a',
                               forecast_summary='n/a', nearest_storm_distance=None, alert_title=None, alert_description=None)


    def __init__(self, key, lat, lon, units, cache_ttl):
        self.key = key
        self.lat = lat
        self.lon = lon
        self.units = units
        self.cache_ttl = cache_ttl


    def cache_name(self):
        return "opeanweather.json"


    def ttl(self):
        return self.cache_ttl


    def acquire(self):
        logging.info("Getting a fresh forecast from the internet using OpenWeather...")

        try:
            r = requests.get(
                "https://api.openweathermap.org/data/2.5/onecall",
                params = {
                    "appid" : self.key,
                    "lat" : self.lat,
                    "lon" : self.lon,
                    "units" : self.units
                }
            )
            return r

        except Exception as e:
            logging.exception(e)

        return None


    def get(self):
        try:
            forecast_data = self.load()
            if forecast_data is None:
                return self.DEFAULT
        
            d = forecast_data['daily'][0]
            
            temp_min = d['temp']['min']
            temp_max = d['temp']['max']

            c = forecast_data['current']

            return OpenWeatherTuple(
                temp=c['temp'],
                temp_min=temp_min,
                temp_max=temp_max,
                icon=c['weather'][0]['icon'] if 'weather' in c else None,
                summary=c['weather'][0]['main'] if 'weather' in c else None,
                forecast_summary=d['weather'][0]['description'] if 'weather' in d else None,
                nearest_storm_distance=None,    # Unsupported by this provider yet
                alert_title=None,               # Unsupported by this provider yet
                alert_description=None          # Unsupported by this provider yet
            )

        except Exception as e:
            logging.exception(e)
            return self.DEFAULT

