# Uses European Meteoalarm.org to provide weather alerts
from acquire import Acquire

import json
import logging
from meteoalertapi import Meteoalert
from collections import namedtuple


MeteoalarmTuple = namedtuple('Meteoalarm', ['provider', 'alert_title', 'alert_description'])


class Meteoalarm(Acquire):

    DEFAULT = MeteoalarmTuple(provider='Meteoalarm.org', alert_title=None, alert_description=None)

    def __init__(self, country, province, cache_ttl):
        self.country = country
        self.province = province
        self.cache_ttl = cache_ttl

    def cache_name(self):
        return "meteoalarm.json"

    def ttl(self):
        return self.cache_ttl

    def error_found(self, status_code, response_text):
        return False

    def acquire(self):
        logging.info("Getting a fresh alarm from Meteoalarm.org...")

        try:
            meteo = Meteoalert(self.country, self.province)
            return 200, json.dumps(meteo.get_alert())

        except Exception as e:
            logging.exception(e)

        return (None, None)

    def get(self):
        try:
            alarm_data = self.load()
            if alarm_data is None:
                return self.DEFAULT
            title = alarm_data['headline'] if 'headline' in alarm_data else None
            title = alarm_data['event'] if not title and 'event' in alarm_data else title

            return MeteoalarmTuple(
                provider='Meteoalarm',
                alert_title=title,
                alert_description=alarm_data['description'] if 'description' in alarm_data else None
            )

        except Exception as e:
            logging.exception(e)
            return self.DEFAULT
