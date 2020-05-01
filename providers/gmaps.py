# Original code: https://github.com/prehensile/waveshare-clock
# Modifications: https://github.com/pskowronek/epaper-clock-and-more, Apache 2 license

from acquire import Acquire

import json
import logging
import requests
from collections import namedtuple


GMapsTuple = namedtuple('Gmaps', ['provider', 'time_to_dest', 'time_to_dest_in_traffic', 'distance', 'origin_address', 'destination_address' ])


class GMaps(Acquire):


    DEFAULT = GMapsTuple(provider='Google Maps', time_to_dest=-1, time_to_dest_in_traffic=-1, distance=-1, origin_address='n/a', destination_address='n/a')    


    def __init__(self, key, home_lat, home_lon, dest_lat, dest_lon, units, name, cache_ttl):
        self.key = key
        self.home_lat = home_lat
        self.home_lon = home_lon
        self.dest_lat = dest_lat
        self.dest_lon = dest_lon
        self.units = units
        self.name = name
        self.cache_ttl = cache_ttl


    def cache_name(self):
        return "gmaps-{}.json".format(self.name)


    def ttl(self):
        return self.cache_ttl


    def error_found(self, status_code, response_text):
        result = False
        if super(GMaps, self).error_found(status_code, response_text):
            result = True
        else:
            response_parsed = json.loads(response_text)
            if 'error_message' in response_parsed:
                logging.warn("GMaps API returned the following error: %s" % response_parsed['error_message'])
                result = True
            elif 'duration_in_traffic' not in response_text:
                logging.warn("GMaps API returned no 'duration_in_traffic' data - probably empty or wrong api key /what a strange API that is/")
                result = True

        return result


    def acquire(self):
        logging.info("Getting time to get to dest: {} from the internet...".format(self.name))

        try:
            r = requests.get(
                "https://maps.googleapis.com/maps/api/distancematrix/json?units={}&departure_time=now&origins={},{}&destinations={},{}&key={}".format(
                    self.units,
                    self.home_lat,
                    self.home_lon,
                    self.dest_lat,
                    self.dest_lon,
                    self.key
                ),
            )
            return r.status_code, r.text
        except Exception as e:
            logging.exception(e)

        return (None, None)


    def get(self):
        try:
            gmaps_data = self.load()
            if gmaps_data is None:
                return self.DEFAULT

            return GMapsTuple(
                provider='Google Maps',
                time_to_dest=gmaps_data['rows'][0]['elements'][0]['duration']['value'],  # in seconds
                time_to_dest_in_traffic=gmaps_data['rows'][0]['elements'][0]['duration_in_traffic']['value'],  # in seconds
                distance=gmaps_data['rows'][0]['elements'][0]['distance']['text'],  # in km, string with km
                origin_address=gmaps_data['origin_addresses'][0],
                destination_address=gmaps_data['destination_addresses'][0]
            )
        except Exception as e:
            logging.exception(e)
            return self.DEFAULT


