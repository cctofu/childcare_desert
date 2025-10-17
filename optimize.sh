#!/bin/bash
set -e
DATA_PATH="./outputs/zipcodes_partial.json"
python ./code/optimize.py "$DATA_PATH"