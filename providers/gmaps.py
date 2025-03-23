# Original code: https://github.com/prehensile/waveshare-clock
# Modifications: https://github.com/pskowronek/epaper-clock-and-more, Apache 2 license

from .acquire import Acquire

import json
import logging
import requests
from collections import namedtuple


GMapsTuple = namedtuple('Gmaps', ['provider', 'time_to_dest', 'time_to_dest_in_traffic', 'distance', 'origin_address', 'destination_address' ])


class GMaps(Acquire):


    DEFAULT = GMapsTuple(provider='Google Maps', time_to_dest=-1, time_to_dest_in_traffic=-1, distance=-1, origin_address='n/a', destination_address='n/a')    


    def __init__(self, key, home_lat, home_lon, home_name, dest_lat, dest_lon, dest_name, units, name, cache_ttl):
        self.key = key
        self.home_lat = home_lat
        self.home_lon = home_lon
        self.home_name = home_name
        self.dest_lat = dest_lat
        self.dest_lon = dest_lon
        self.dest_name = dest_name
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
            if 'error' in response_parsed:
                logging.warn("GMaps API returned the following error: %s" % response_parsed['error_message'])
                result = True
            elif 'duration' not in response_text:
                logging.warn("GMaps API returned no 'duration' data - probably empty or wrong api key.")
                result = True

        return result


    def acquire(self):
        logging.info("Getting time to get to dest: {} from the internet...".format(self.name))

        body = { 
            'units': self.units,
            #'departureTime': Timestamp in UTC - defaults to now
            'origins': [
                {
                    'waypoint': {
                        'location': {
                            'latLng': {
                                'latitude': self.home_lat,
                                'longitude': self.home_lon
                            }
                        }
                    },
                }
            ],
            'destinations': [
                {
                    'waypoint': {
                        'location': {
                            'latLng': {
                                'latitude': self.dest_lat,
                                'longitude': self.dest_lon
                            }
                        }
                    },
                }
            ],
            'travelMode': 'DRIVE',
            'routingPreference': 'TRAFFIC_AWARE'
        }

        try:
            r = requests.post(
                "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
                headers = { 'X-Goog-Api-Key': self.key, 'X-Goog-FieldMask': 'duration,staticDuration,distanceMeters,status'},
                json = body,
                timeout=(2, 4)
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
                time_to_dest=int(gmaps_data[0]['staticDuration'].rstrip('s')),  # in seconds
                time_to_dest_in_traffic=int(gmaps_data[0]['duration'].rstrip('s')),  # in seconds
                distance='{} km'.format(int(gmaps_data[0]['distanceMeters'])/1000),  # in km, string with km
                origin_address=self.home_name,
                destination_address=self.dest_name
            )
        except Exception as e:
            logging.exception(e)
            return self.DEFAULT


