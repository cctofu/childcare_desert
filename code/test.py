import json 
from structs.zipcode import Zipcodes

with open('./outputs/zipcodes_partial.json', "r") as f:
        data = json.load(f)

zip = Zipcodes(data)
zip.print_summary()