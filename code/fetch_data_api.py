import requests
from typing import Any, Dict
import json
from tqdm import tqdm
import colorful as cf
from structs.zipcode import Zipcodes
from utils import normalize_zip
import sys
cf.use_style('monokai')

ACS_YEAR = "2023"
BASE_DETAILED = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5"
BASE_SUBJECT  = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5/subject"
BASE_PROFILE = f"https://api.census.gov/data/{ACS_YEAR}/acs/acs5/profile"
VARS_DETAILED = ["NAME", "B01003_001E", "B19301_001E"]  
VARS_SUBJECT  = ["S2301_C03_001E"]                     

def _get_json(base_url: str, params: Dict[str, str]) -> Dict[str, Any]:
    api_key = "a07e88f5c9cfb9e4790f66f53fa31f93010921ec" 
    q = {**params, "key": api_key} 
    r = requests.get(base_url, params=q, timeout=20)
    if r.status_code == 204:
        return {} 
    if r.status_code != 200:
        print(f"⚠️ Census API error {r.status_code}: No results for URL={r.url}")
        return {}
    try:
        data = r.json()
    except Exception:
        print(f"⚠️ Non-JSON response from {r.url}")
        return {}
    if not isinstance(data, list) or len(data) < 2:
        return {}

    headers = data[0]
    row = data[1]
    return dict(zip(headers, row))


def _to_float_or_zero(x: Any) -> Any:
    try:
        if x in (None, "", "null", -666666666.0, "-666666666.0"):
            return 0
        return float(x)
    except Exception:
        return 0

def safe_int(x):
    try:
        if x in (None, "", "null"):
            return 0
        return int(float(x))
    except Exception:
        return 0

def fetch_data(data):
    zipcodes = Zipcodes(data)
    missing_data = zipcodes.get_missing_data()
    income_changed = 0
    employment_changed = 0
    population0_5_changed = 0
    population0_12_changed = 0
    for key in tqdm(missing_data):
        missing_values = zipcodes.get_missing_values(key)
        data = {}
        for m in missing_values:
            z = normalize_zip(key)
            if m == 0:
                income = _get_json(
                    BASE_DETAILED,
                    {"get": ",".join(VARS_DETAILED), "for": f"zip code tabulation area:{z}"},
                )
                average_income = _to_float_or_zero(income.get("B19301_001E"))
                if average_income != 0:
                    data['avg_individual_income'] = average_income
                    income_changed += 1
            elif m == 1:
                employment = _get_json(
                    BASE_SUBJECT,
                    {"get": ",".join(VARS_SUBJECT), "for": f"zip code tabulation area:{z}"},
                )
                employment_rate = _to_float_or_zero(employment.get("S2301_C03_001E"))
                if employment_rate != 0:
                    data['employment_rate'] = employment_rate
                    employment_changed += 1
            else:
                age_vars = {
                    "age0_4": "DP05_0005E",
                    "age5_9": "DP05_0006E",
                    "age10_14": "DP05_0007E",
                }
                dp05 = _get_json(
                    BASE_PROFILE,
                    {"get": ",".join(["NAME"] + list(age_vars.values())),
                    "for": f"zip code tabulation area:{z}"}
                )
                pop0_5 = safe_int(dp05.get(age_vars["age0_4"]))
                pop5_9 = safe_int(dp05.get(age_vars["age5_9"]))
                pop10_14 = safe_int(dp05.get(age_vars["age10_14"]))
                pop0_12 = pop0_5 + pop5_9 + (2/3)*pop10_14
                if pop0_5 != 0:
                    data['population0_5'] = pop0_5
                    data['population0_12'] = pop0_12
                    population0_5_changed += 1
                    population0_12_changed += 1
        zipcodes.modify_zipcode_values(key, data)
    print(cf.bold(cf.seaGreen(f'Added {cf.yellow(income_changed)} missing <average income> values')))
    print(cf.bold(cf.seaGreen(f'Added {cf.yellow(employment_changed)} missing <employment rate> values')))
    print(cf.bold(cf.seaGreen(f'Added {cf.yellow(population0_5_changed)} missing <population 0 to 5> values')))
    print(cf.bold(cf.seaGreen(f'Added {cf.yellow(population0_12_changed)} missing <population 0 to 12> values')))
    return zipcodes

if __name__ == "__main__":
    in_path = sys.argv[1] 
    out_path = sys.argv[2] 
    print(cf.bold(cf.seaGreen(f"Got zipcode data from: {cf.yellow(in_path)}")))
    print(cf.bold(cf.seaGreen('Attempting to fetch zipcode data...')))
    with open(in_path, "r") as f:
        data = json.load(f)
    zipcodes = fetch_data(data)
    zipcodes.save_data_to_path(out_path)
    print(cf.bold(cf.seaGreen('Completed successfully')))
    print(cf.bold(cf.seaGreen(f"Saved data to: {cf.yellow(out_path)}")))
    zipcodes.print_summary()