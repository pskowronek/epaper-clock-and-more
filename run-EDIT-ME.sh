#!/bin/bash

# This script is to either:
# - test and trial run epaper-clock-and-more manually
# - be luanched by provided epaper.service (that must be registered under /etc/systemd - your mileage may vary depending what distribution you use)
#
# Please read README.md first to understand what is the meaning the variables below.
#

# WARNING WARNING WARNING
# - rename run-EDIT-ME.sh to run.sh and comment out the following 2 lines and re-configure the environment variables below
echo "Please edit and configure this script for your needs"
exit 1

# Developer debug mode - no epaper device is required to develop or debug - the output that is originally 
# sent to device is being saved as bmp files here: /tmp/epaper*.bmp
#export EPAPER_DEBUG_MODE=true

# Experimental modification of LUT tables that form waveforms that refresh "pixels" - implemented only for 2.7" displays.
# This modification makes refresh about 10 times faster for black die, and 2-3 times faster for red die. This of course has
# consequences in not-so ideal refresh and with time some random artifacts may start to build up. To recover you would need
# to turn this feature off for some time until original LUT tables won't remove those artifacts.
# Enable this feature on your own responsibility!
#export EPAPER_FAST_REFRESH=true

# Lat & lon of your home (a base point)
export LAT=50.0720519
export LON=20.0373204

# A key for traffic delays from Google Maps Distance Matrix API
export GOOGLE_MAPS_KEY=GET_YOUR_OWN_KEY     # get the key from: https://developers.google.com/maps/documentation/embed/get-api-key
# A key for weather forecasts from OpenWeather One Call API
export OPENWEATHER_KEY=GET_YOUR_OWN_KEY  # get the key from: https://openweathermap.org/home/sign_up
# A key for AQI (Air Quality Index) from AIRLY.EU API (data for certain countries only, as yet, but you may order their device to provide data also for your neighbours)
export AIRLY_KEY=GET_YOUR_OWN_KEY           # get the key from: https://developer.airly.eu/register
# A key for AQI (Air Quality Index) from AQICN API (data for cities across the world) - used as a fallback if Airly key above is not defined.
# See AQICN_CITY_OR_ID below to optionally specify city instead of lat&lon as above, or to use IP based geolocation.
export AQICN_KEY=GET_YOUR_OWN_KEY           # get the key from: https://aqicn.org/data-platform/token/


# A key for weather forecasts from DarkSky.net API (deprecated as is no longer possible to acquire new keys from DarkSky - existing keys should work until the end of 2021, https://blog.darksky.net/)
export DARKSKY_KEY=GET_YOUR_OWN_KEY         # get the key from: https://darksky.net/dev/register - deprecated (pending removal in 2022)


# Cache TTLs in minutes for each data fetcher (refer to free accounts limitations before you change the values any lower than 10m)
export GOOGLE_MAPS_TTL=10
export AIRLY_TTL=20
export AQICN_TTL=20
export OPENWEATHER_TTL=15
export DARKSKY_TTL=15                       # deprecated (pending removal in 2022)

# AQICN City or ID (see: https://aqicn.org/search/) to use instead of LAT&LON coords, if you set it to 'here' then it is going to be based on IP geolocation
#export AQICN_CITY_OR_ID=here

# Units
export GOOGLE_MAPS_UNITS=metric             # refer to: https://developers.google.com/maps/documentation/distance-matrix/intro#unit_systems for allowed values (metric, imperial)
export OPENWEATHER_UNITS=metric             # refer to: https://openweathermap.org/api/one-call-api#data for allowed values (metric, imperial, etc)
export DARK_SKY_UNITS=si                    # refer to: https://darksky.net/dev/docs for allowed values (si, us, auto, etc) - deprecated (pending removal in 2022)

# Warning levels
export AQI_WARN_LEVEL=75                    # above this value the displayed gauge will become red (on supported displays)
export WEATHER_STORM_DISTANCE_WARN=10       # display warning if storm is closer than this value in km/miles (take a look at units above) - if supported by weather provider

# Lat & lon of destination you want to calculate the current driving time including traffic
export FIRST_TIME_TO_DESTINATION_LAT=49.9823219
export FIRST_TIME_TO_DESTINATION_LON=20.0578518
# The displayed gauge will become red (on supported displays) when driving time exceeds by % 
export FIRST_TIME_WARN_ABOVE_PERCENT=50

# Lat & lon of second destination (for a second member of a household?) you want to calculate the current driving time including traffic
export SECOND_TIME_TO_DESTINATION_LAT=49.9684476
export SECOND_TIME_TO_DESTINATION_LON=20.4303646
# The displayed gauge will become red (on supported displays) when driving time exceeds by % 
export SECOND_TIME_WARN_ABOVE_PERCENT=50

# Whether to paint black font on red canvas (for warn statuses) - helps visual espect if red dye faded out already
export WARN_PAINTED_BLACK_ON_RED=false

# Dead times - between stated hours data & display update is being done once in an hour and minutes won't be displayed. Default is [] - no dead times.
# This env var will be evaluated by python - so becareful, first: don't expose this env to outside world (security), second: follow the syntax otherwise program will die
#export DEAD_TIMES="[range(1,5),range(10,15)]"

# Whether to draw two vertical dots to separate hours and minutes (to avoid confusion that a year is being displayed... yes, I know people who first thought that was a year displayed)
export CLOCK_HRS_MINS_SEPARATOR=true

# Whether to prefer Airly.eu local temperature if available instead of current temperature returned by weather provider. Metric (Celsius) temperature only.
#export PREFER_AIRLY_LOCAL_TEMP=false

# A type of EPAPER display you want to use - either Waveshare 4"2 (b&w) or 2"7 (tri-color) - this automatically sets EPAPER_MONO to "true" for 2"7 and to "false" for 4"2
#export EPAPER_TYPE=waveshare-4.2
export EPAPER_TYPE=waveshare-2.7
# You can override the setting as whether the display is mono or not - though, it will require update (replacement) of relevant epdXinX.py library to support mono or tri-color
#export EPAPER_MONO=true
# You can override whether to listen for button press (enabled by default)
#export EPAPER_BUTTONS_ENABLED=true
# You can override GPIO pins assigned to buttons (these values are set by default and reflect 2.7" HUT version)
#export EPAPER_GPIO_PIN_FOR_KEY1=5
#export EPAPER_GPIO_PIN_FOR_KEY2=6
#export EPAPER_GPIO_PIN_FOR_KEY3=13
#export EPAPER_GPIO_PIN_FOR_KEY4=19

python main.py
