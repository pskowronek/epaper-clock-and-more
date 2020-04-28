# https://github.com/pskowronek/epaper-clock-and-more, Apache 2 license

from acquire import Acquire

import psutil
from uptime import uptime

import logging
from collections import namedtuple


SystemTuple = namedtuple('SystemInfo', ['provider', 'uptime', 'cpu_usage', 'mem_usage', 'free_disk'])


class SystemInfo(Acquire):


    DEFAULT = SystemTuple(provider='System', uptime="n/a", cpu_usage="n/a", mem_usage="n/a", free_disk="n/a")


    def __init__(self, cache_ttl = -1):
        self.cache_ttl = cache_ttl


    def cache_name(self):
        return "system-info.json"


    def ttl(self):
        return self.cache_ttl


    def get(self):
        try:
            return SystemTuple(
                provider='System',
                uptime="{:0.0f} days".format(uptime() / (3600 * 24)),
                cpu_usage="{} %".format(psutil.cpu_percent()),
                mem_usage="{} %".format(psutil.virtual_memory().percent),
                free_disk="{} MB".format(psutil.disk_usage('/').free / (1024 * 1024))
            )

        except Exception as e:
            logging.exception(e)
            return self.DEFAULT


