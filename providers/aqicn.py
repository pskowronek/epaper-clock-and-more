# AQICN.org (Air Quality Open Data Platform) - a provider of AQI througout a world (an alternative /a fallback/ for Airly which is more popular in Central Europe)

from acquire import Acquire

import logging
import requests
from collections import namedtuple


AqicnTuple = namedtuple('Aqicn', ['pm25', 'pm10', 'hummidity', 'pressure', 'temperature', 'aqi', 'level', 'advice'])


class Aqicn(Acquire):


    DEFAULT = AqicnTuple(pm25=-1, pm10=-1, pressure=-1, hummidity=-1, temperature=None, aqi=-1, level='n/a', advice='n/a')


    def __init__(self, key, lat, lon, city_or_id, cache_ttl):
        self.key = key
        self.lat = lat
        self.lon = lon
        self.city_or_id = city_or_id
        self.cache_ttl = cache_ttl


    def cache_name(self):
        return "aqicn.json"


    def ttl(self):
        return self.cache_ttl


    def acquire(self):
        logging.info("Getting a Aqicn status from the internet...")

        try:
            r = requests.get(
                "https://api.waqi.info/feed/{}/?token={}".format(
                    self.city_or_id if self.city_or_id else "geo:{};{}".format(self.lat, self.lon),
                    self.key
                )
            )
            return r
        except Exception as e:
            logging.exception(e)

        return None


    def get(self):
        try:
            aqicn_data = self.load()
            if aqicn_data is None or aqicn_data["status"] != 'ok':
                logging.warn("No reasonable data returned by Aqicn. Check API key (status code) or whether the given city/id/lon&lat is known and handled by the service (visit: https://aqicn.org/search/)")
                return self.DEFAULT

            return AqicnTuple(
                pm25=aqicn_data["data"]["iaqi"]["pm25"]["v"] if aqicn_data["data"]["iaqi"]["pm25"] else -1,
                pm10=aqicn_data["data"]["iaqi"]["pm10"]["v"] if aqicn_data["data"]["iaqi"]["pm10"] else -1,
                pressure=aqicn_data["data"]["iaqi"]["p"]["v"] if aqicn_data["data"]["iaqi"]["p"] else -1,
                hummidity=aqicn_data["data"]["iaqi"]["h"]["v"] if aqicn_data["data"]["iaqi"]["h"] else -1,
                temperature=aqicn_data["data"]["iaqi"]["t"]["v"] if aqicn_data["data"]["iaqi"]["t"] else None,
                aqi=aqicn_data["data"]["aqi"],
                level=None,
                advice=None
            )

        except Exception as e:
            logging.exception(e)
            return self.DEFAULT


