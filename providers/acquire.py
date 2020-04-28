# Original code: https://github.com/prehensile/waveshare-clock
# Modifications: https://github.com/pskowronek/epaper-clock-and-more, Apache 2 license

import logging

import json
import os
import time


class Acquire(object):


    def cache_name(self):
        pass


    def cache_path(self):
        pth_cache = os.path.expanduser("~/.epaper-display/cache/")
        if not os.path.exists(pth_cache):
            os.makedirs(pth_cache)
        return os.path.join(pth_cache, self.cache_name())


    def ttl(self):
        return 10  # default 10 minutes


    def load_cached(self):
        fn_cache = self.cache_path()
        if os.path.exists(fn_cache):
            logging.info("Loading cache file: %s %s" % (fn_cache, str(type(self))))
            with open(fn_cache) as fp:
                return json.load(fp)

        return None


    def get_cache_ts(self):
        fn_cache = self.cache_path()
        if os.path.exists(fn_cache):
            return os.path.getmtime(fn_cache)
        return None


    def acquire(self):
        pass


    def error_found(self, status_code, response_text):
        result = False
        if (status_code in [401, 403] ):
            logging.warn("Remote server returned: %d - probably wrong API key" % status_code)
            result = True
        elif (status_code != 200):
            logging.warn("Remote server returned unexpected status code: %d" % status_code)
            result = True

        return result


    def load_and_cache(self):
        acquired_data = None
        status_code, response_text = self.acquire()
        if status_code is not None:
            if not self.error_found(status_code, response_text):
                acquired_data = json.loads(response_text)
                # write just acquired data to cache
                fn_cache = self.cache_path()
                with open(fn_cache,'wb') as fp:
                    fp.write(response_text.encode('utf-8'))
        return acquired_data


    def load(self):
        # start from cached data 
        acquired_data = self.load_cached()

        # no data has been cached yet
        if acquired_data is None:
            logging.info("No cache found - acquiring data... %s" % str(type(self)))
            acquired_data = self.load_and_cache()
        else:
            # get last modified time for cache...
            ts_cache = self.get_cache_ts()

            # refresh every TTL in minutes
            if ts_cache is not None:
                now = time.time()
                if (now - ts_cache) > 60 * self.ttl():
                    logging.info("Cache too old, renewing...")
                    acquired_data = self.load_and_cache()

        return acquired_data


    def get(self):
        pass

