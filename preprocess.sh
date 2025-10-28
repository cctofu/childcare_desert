#!/bin/bash
set -e

# Activate your virtual environment if needed
# conda activate optimization

# Create dataset
OUT_PATH="./outputs/zipcodes_partial.json"
#python ./code/create_zipcodes.py "$OUT_PATH"
OUT_PATH2="./ouputs/zipcodes_filled_1.json"
python ./code/fetch_data_api.py "$OUT_PATH" "$OUT_PATH2"
#python ./code/check_zipcodes.py ./outputs/zipcodes_filled_1.json