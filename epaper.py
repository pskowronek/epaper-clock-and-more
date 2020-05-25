# Original code: https://github.com/prehensile/waveshare-clock
# Modifications: https://github.com/pskowronek/epaper-clock-and-more, Apache 2 license

import logging
import json
import os
from PIL import Image

from drawing import Drawing
from providers.airly import Airly
from providers.aqicn import Aqicn

from providers.openweather import OpenWeather
from providers.weatherbit import Weatherbit
from providers.darksky import DarkSky

from providers.meteoalarm import Meteoalarm

from providers.gmaps import GMaps
from providers.system_info import SystemInfo


class EPaper(object):

    # only update once an hour within these ranges
    # eval - don't try this at home :) i.e. don't expose envs to alians
    DEAD_TIMES = eval(os.environ.get("DEAD_TIMES", "[]"))
    # whether to display two vertical dots to separate hrs and mins
    CLOCK_HOURS_MINS_SEPARATOR = os.environ.get("CLOCK_HRS_MINS_SEPARATOR", "true") == "true"
    # whether to prefer AQI temperature instead of DarkSky's
    PREFER_AIRLY_LOCAL_TEMP = os.environ.get("PREFER_AIRLY_LOCAL_TEMP", "false") == "true"
    # warn states painted black instead of white on red canvas?
    WARN_PAINTED_BLACK_ON_RED = os.environ.get("WARN_PAINTED_BLACK_ON_RED", "false") == "true"

    DEVICE_TYPE = os.environ.get("EPAPER_TYPE", 'waveshare-2.7')


    if DEVICE_TYPE == 'waveshare-2.7':          # TODO refactor to use enums
        # Display resolution for 2.7"
        EPD_WIDTH       = 176
        EPD_HEIGHT      = 264
        MONO_DISPLAY    = False
    elif DEVICE_TYPE == 'waveshare-4.2':
        # Display resolution for 4.2"
        EPD_WIDTH       = 400
        EPD_HEIGHT      = 300
        MONO_DISPLAY    = True
    else:
        raise Exception('Incorrect epaper screen type: ' + DEVICE_TYPE)


    MONO_DISPLAY = os.environ.get("EPAPER_MONO", "true" if MONO_DISPLAY else "false") == "true"  # one may override but must replace relevant library edpXinX.py, by default lib for 2.7 is tri-color, 4.2 is mono
    FAST_REFRESH = os.environ.get("EPAPER_FAST_REFRESH", "false") == "true"


    drawing = Drawing(
        os.environ.get("DARK_SKY_UNITS", "si"),
        int(os.environ.get("WEATHER_STORM_DISTANCE_WARN", "10")),
        int(os.environ.get("AQI_WARN_LEVEL", "75")),
        int(os.environ.get("FIRST_TIME_WARN_ABOVE_PERCENT", "50")),
        int(os.environ.get("SECONDARY_TIME_WARN_ABOVE_PERCENT", "50"))
    )

    aqi = None
    if os.environ.get("AIRLY_KEY"):
        aqi = Airly(
            os.environ.get("AIRLY_KEY"),
            os.environ.get("LAT"),
            os.environ.get("LON"),
            int(os.environ.get("AIRLY_TTL", "20"))
        )
    else:
        aqi = Aqicn(
            os.environ.get("AQICN_KEY"),
            os.environ.get("LAT"),
            os.environ.get("LON"),
            os.environ.get("AQICN_CITY_OR_ID"),
            int(os.environ.get("AQICN_TTL", "20"))
        )

    weather = None
    if os.environ.get("OPENWEATHER_KEY"):
        weather = OpenWeather(
            os.environ.get("OPENWEATHER_KEY"),
            os.environ.get("LAT"),
            os.environ.get("LON"),
            os.environ.get("OPENWEATHER_UNITS", "metric"),
            int(os.environ.get("OPENWEATHER_TTL", "15"))
        )
    elif os.environ.get("WEATHERBIT_IO_KEY"):
        weather = Weatherbit(
            os.environ.get("WEATHERBIT_IO_KEY"),
            os.environ.get("LAT"),
            os.environ.get("LON"),
            os.environ.get("WEATHERBIT_IO_UNITS", "M"),
            int(os.environ.get("WEATHERBIT_IO_TTL", "15"))
        )
    else:
        weather = DarkSky(
            os.environ.get("DARKSKY_KEY"),
            os.environ.get("LAT"),
            os.environ.get("LON"),
            os.environ.get("DARKSKY_UNITS", "si"),
            int(os.environ.get("DARKSKY_TTL", "15"))
        )

    meteoalarm = None
    if os.environ.get('METEOALARM_COUNTRY') and os.environ.get('METEOALARM_PROVINCE'):
        meteoalarm = Meteoalarm(
            os.environ.get("METEOALARM_COUNTRY").decode('utf-8'),
            os.environ.get("METEOALARM_PROVINCE").decode('utf-8'),
            int(os.environ.get("METEOALARM_TTL", "15"))
        )

    gmaps1 = GMaps(
        os.environ.get("GOOGLE_MAPS_KEY"),
        os.environ.get("LAT"),
        os.environ.get("LON"),
        os.environ.get("FIRST_TIME_TO_DESTINATION_LAT"),
        os.environ.get("FIRST_TIME_TO_DESTINATION_LON"),
        os.environ.get("GOOGLE_MAPS_UNITS", "metric"),
        "primary",
        int(os.environ.get("GOOGLE_MAPS_TTL", "10"))
    )
    gmaps2 = GMaps(
        os.environ.get("GOOGLE_MAPS_KEY"),
        os.environ.get("LAT"),
        os.environ.get("LON"),
        os.environ.get("SECOND_TIME_TO_DESTINATION_LAT"),
        os.environ.get("SECOND_TIME_TO_DESTINATION_LON"),
        os.environ.get("GOOGLE_MAPS_UNITS", "metric"),
        "secondary",
        int(os.environ.get("GOOGLE_MAPS_TTL", "10"))
    )
    system_info = SystemInfo()


    def __init__(self, debug_mode = False):

        self._debug_mode = debug_mode
        if not debug_mode:
            if self.DEVICE_TYPE == 'waveshare-2.7':
                if self.FAST_REFRESH:
                    logging.info("Using experimental LUT tables!")
                    from epds import epd2in7b_fast_lut
                    self._epd = epd2in7b_fast_lut.EPD()
                else:
                    from epds import epd2in7b
                    self._epd = epd2in7b.EPD()
            elif self.DEVICE_TYPE == 'waveshare-4.2':
                from epds import epd4in2
                self._epd = epd4in2.EPD()

            self._epd.init()

        self._str_time = "XXXX"


    def display(self, black_buf, red_buf, name):
        if self._debug_mode:
            debug_output = "/tmp/epaper-" + ( name.strftime("%H-%M-%S") if type(name) is not str else name )
            logging.info("Debug mode - saving screen output to: " + debug_output + "* bmps")
            black_buf.save(debug_output + "_bw_frame.bmp")
            red_buf.save(debug_output + "_red_frame.bmp")
            return

        if not self.MONO_DISPLAY:
            logging.info("Going to display a new tri-color image...")
            self._epd.display_frame(
                self._epd.get_frame_buffer(black_buf),
                self._epd.get_frame_buffer(red_buf)
            )
        else:
            logging.info("Going to display a new mono-color image...")
            self._epd.display_frame(
                self._epd.get_frame_buffer(black_buf)
            )


    def display_buffer(self, black_buf, red_buf, dt):

        if self.DEVICE_TYPE == 'waveshare-2.7':
            black_buf = black_buf.transpose(Image.ROTATE_90)
            black_buf = black_buf.resize((self.EPD_WIDTH, self.EPD_HEIGHT), Image.LANCZOS)

            red_buf = red_buf.transpose(Image.ROTATE_90)
            red_buf = red_buf.resize((self.EPD_WIDTH, self.EPD_HEIGHT), Image.LANCZOS)

        self.display(black_buf, red_buf, dt)


    def display_shutdown(self):
        black_frame, red_frame = self.drawing.draw_shutdown(self.MONO_DISPLAY)
        self.display_buffer(black_frame, red_frame, 'shutdown')


    def display_aqi_details(self):
        black_frame, red_frame = self.drawing.draw_aqi_details(self.aqi.get())
        self.display_buffer(black_frame, red_frame, 'aqi')


    def display_gmaps_details(self):
        black_frame, red_frame = self.drawing.draw_gmaps_details(self.gmaps1.get(), self.gmaps2.get())
        self.display_buffer(black_frame, red_frame, 'gmaps')


    def display_weather_details(self):
        black_frame, red_frame = self.drawing.draw_weather_details(self.merge_weather_and_meteo(self.weather, self.meteoalarm))
        self.display_buffer(black_frame, red_frame, 'weather')


    def display_system_details(self):
        black_frame, red_frame = self.drawing.draw_system_details(self.system_info.get())
        self.display_buffer(black_frame, red_frame, 'system')

    def cycle_display(self):
        black_frame, red_frame, white_frame = self.drawing.draw_blanks()
        for cycle in range(1, 3):
            self.display_buffer(black_frame, white_frame, '')
            for cycle_reds in range(1, 10):
                self.display_buffer(white_frame, red_frame, '')
            self.display_buffer(white_frame, white_frame, '')

    def display_main_screen(self, dt, force = False):
        time_format = "%H%M"
        formatted = dt.strftime(time_format)

        # set blank minutes if time's hour is within dead ranges
        h = formatted[:2]
        for dead_range in self.DEAD_TIMES:
            if int(h) in dead_range:
                formatted = "{}  ".format(h)

        if force or formatted != self._str_time:

            weather_data = self.merge_weather_and_meteo(self.weather, self.meteoalarm)
            logging.info("--- weather: " + json.dumps(weather_data))

            aqi_data = self.aqi.get()
            logging.info("--- aqi: " + json.dumps(aqi_data))

            gmaps1_data = self.gmaps1.get()
            logging.info("--- gmaps1: " + json.dumps(gmaps1_data))

            gmaps2_data = self.gmaps2.get()
            logging.info("--- gmaps2: " + json.dumps(gmaps2_data))

            black_frame, red_frame = self.drawing.draw_frame(
                self.MONO_DISPLAY,
                formatted,
                self.CLOCK_HOURS_MINS_SEPARATOR,
                weather_data,
                self.PREFER_AIRLY_LOCAL_TEMP,
                self.WARN_PAINTED_BLACK_ON_RED,
                aqi_data,
                gmaps1_data,
                gmaps2_data
            )
            self.display_buffer(black_frame, red_frame, dt)

            self._str_time = formatted

    def merge_weather_and_meteo(self, weather, meteoalarm):
        w = weather.get()
        result = w
        if meteoalarm:
            m = meteoalarm.get()
            result = w._replace(provider = "%s & %s" % (w.provider, m.provider) if m.alert_title or m.alert_description else w.provider,
                                alert_title = w.alert_title if w.alert_title else m.alert_title,
                                alert_description = w.alert_description if w.alert_description else m.alert_description)
        return result
