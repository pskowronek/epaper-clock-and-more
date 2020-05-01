##
#  @filename   :   main.cpp
#  @brief      :   4.2inch e-paper display demo
#  @author     :   Yehui from Waveshare
#
#  Copyright (C) Waveshare     July 28 2017
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
##

# Original code: https://github.com/prehensile/waveshare-clock
# Modifications: https://github.com/pskowronek/epaper-clock-and-more, Apache 2 license

import os
import sys
import logging
import logging.handlers
import signal
import atexit
import sdnotify

import time
from pytz import timezone
from datetime import datetime
from tzlocal import get_localzone

from epaper import EPaper

# debugging aka developer mode (even w/o e-paper display and rpi)
DEBUG_MODE = os.environ.get("EPAPER_DEBUG_MODE", "false") == "true"
EPAPER_DEBUG_MODE_DONT_LOOP = os.environ.get("EPAPER_DEBUG_MODE_DONT_LOOP", "false") == "true"

shutting_down = False
details_to_display = None
epaper = None


def main():
    global epaper
    global shutting_down
    global details_to_display

    epaper = EPaper(debug_mode=DEBUG_MODE)

    atexit.register(shutdown_hook)
    signal.signal(signal.SIGTERM, signal_hook)

    buttons = None
    if not DEBUG_MODE and (os.environ.get("EPAPER_BUTTONS_ENABLED", "true") == "true"):
        from buttons import Buttons
        buttons = Buttons(
            [
                int(os.environ.get("EPAPER_GPIO_PIN_FOR_KEY1", "5")),
                int(os.environ.get("EPAPER_GPIO_PIN_FOR_KEY2", "6")),
                int(os.environ.get("EPAPER_GPIO_PIN_FOR_KEY3", "13")),
                int(os.environ.get("EPAPER_GPIO_PIN_FOR_KEY4", "19"))
            ],
            lambda key: action_button(key, epaper)
        )

    notifier = sdnotify.SystemdNotifier()
    notifier.notify("READY=1")

    while True:
        if shutting_down:
            logging.info("App is shutting down.....")
            break

        notifier.notify("WATCHDOG=1")

        if details_to_display is not None:
            logging.info("Going to refresh the main screen with details view...")
            details_to_display()
            details_to_display = None
            buttons.set_not_busy()
            for i in range(10):
                time.sleep(0.5)
                if details_to_display is not None:
                    logging.info("Got button pressed while in details!")
                    break
            if details_to_display is not None:
                continue
            logging.info("Ok, enough - going back to standard view")
            refresh_main_screen(epaper, force = True)
        else:
            logging.info("Going to refresh the main screen...")
            refresh_main_screen(epaper)

        if EPAPER_DEBUG_MODE_DONT_LOOP:
            shutting_down = True

        for i in range(120 if buttons is not None else 1):  # lower the CPU usage when no buttons handled
            if shutting_down:
                logging.info("App is shutting down...")
                break
            if details_to_display is not None:
                logging.info("Got button pressed!")
                break
            time.sleep(0.5 if buttons is not None else 60)


def action_button(key, epaper):
    global details_to_display
    if key == 1:
        details_to_display = lambda: epaper.display_gmaps_details()
    elif key == 2:
        details_to_display = lambda: epaper.display_aqi_details()
    elif key == 3:
        details_to_display = lambda: epaper.display_weather_details()
    elif key == 4:
        details_to_display = lambda: epaper.display_system_details()
    else:
        details_to_display = None


def refresh_main_screen(epaper, force = False):
    utc_dt = datetime.now(timezone('UTC'))  # time readings should be done in epaper itself (probably using acquire.py w/o caching)
    epaper.display_main_screen(utc_dt.astimezone(get_localzone()), force)
    if DEBUG_MODE:
        epaper.display_weather_details()
        epaper.display_aqi_details()
        epaper.display_gmaps_details()
        epaper.display_system_details()


def signal_hook(*args):
    if shutdown_hook():
        logging.info("calling exit 0")
        sys.exit(0) 


def shutdown_hook():
    global epaper
    global shutting_down
    if shutting_down:
        return False
    shutting_down = True
    logging.info("You are now leaving the Python sector - the app is being shutdown.")
    if epaper is not None:
        logging.info("...but, let's try to display shutdown icon")
        epaper.display_shutdown()
        logging.info("...finally going down")
    return True


def init_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(handler)
    
    if not DEBUG_MODE:
        log_address = '/var/run/syslog' if sys.platform == 'darwin' else '/dev/log'
        formatter = logging.Formatter('EPaper: %(message)s')
        handler = logging.handlers.SysLogHandler(address=log_address)
        handler.setFormatter(formatter)


if __name__ == '__main__':
    init_logging()
    try:
        main()
    except Exception as e:
        logging.exception(e)
        raise
