import json
from structs.zipcode import Zipcodes

# Path to your JSON file
file_path = "./outputs/zipcodes_partial.json"

# Load the file
with open(file_path, "r") as f:
    data = json.load(f)

z = Zipcodes(data)
# Print the number of entries
print("Number of ZIP codes:", z.get_missing_data_length())
print("Number of ZIP codes:", z.get_complete_data_length())