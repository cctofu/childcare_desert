#!/bin/bash
set -e

# Activate your virtual environment if needed
# conda activate optimization

# Create dataset
OUT_PATH="./outputs/zipcodes_partial.json"
python ./code/create_zipcodes.py "$OUT_PATH"
OUT_PATH2="./outputs/zipcodes_filled_1.json"
python ./code/fetch_data_api.py "$OUT_PATH" "$OUT_PATH2"

# Run Optimization
BIN_SIZE=20
DATA_PATH="./outputs/zipcodes_partial.json"
PLOT_ON=false
python ./code/optimize.py "$DATA_PATH" $BIN_SIZE $PLOT_ON