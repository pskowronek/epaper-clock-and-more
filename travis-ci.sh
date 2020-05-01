#!/bin/bash

# TRAVIS CI script - don't use it for "production" - it is only to run sanity check on travis-ci.org

export EPAPER_DEBUG_MODE=true
export EPAPER_DEBUG_MODE_DONT_LOOP=true


python main.py
