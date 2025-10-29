#!/bin/bash
set -e

DATA_PATH="./outputs/zipcodes_filled_1.json"
ZCTA_PATH="./extra_data/cb_2018_us_zcta510_500k/cb_2018_us_zcta510_500k.shp"
python ./code/optimize.py "$DATA_PATH" "$ZCTA_PATH"