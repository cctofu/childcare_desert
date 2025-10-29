#!/bin/bash
set -e

# Run optimization based on data path
BIN_SIZE=20
DATA_PATH="./outputs/zipcodes_filled_1.json"
python ./code/optimize.py "$DATA_PATH" $BIN_SIZE