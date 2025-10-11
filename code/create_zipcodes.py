import os
import json
import pandas as pd
import colorful as cf
from collections import defaultdict
from tqdm import tqdm
import numpy as np

cf.use_style('monokai')
DATA_DIR = "./data"
FILE_MAP= {
    "avg_individual_income.csv": "ZIP code",
    "child_care_regulated.csv": "zip_code",
    "employment_rate.csv": "zipcode",
    "population.csv": "zipcode",
    "potential_locations.csv": "zipcode",
}

'''
Ensure zipcode is 5 digits, trim to 5 if longer than 5
'''
def normalize_zip(z):
    s = str(z).strip()
    s = s[:5] if len(s) > 5 else s
    return s if s else None


'''
Load data path and make dataframe
'''
def load_csv(path, zip_col):
    df = pd.read_csv(path)
    df = df.copy()
    df[zip_col] = df[zip_col].map(normalize_zip)
    df = df.dropna(subset=[zip_col])
    return df


'''
Find zipcodes that exist within all 5 data files
'''
def find_zipcode_intersection():
    intersection = None
    for fname, zcol in FILE_MAP.items():
        path = os.path.join(DATA_DIR, fname)
        df = load_csv(path, zcol)
        zips = set(df[zcol].astype(str))
        if intersection:
            intersection &= zips
        else:
            intersection = zips
    return intersection, len(intersection)


'''
Build dictionary with keys as zipcode values
'''
def build_filled_zip_dict(valid_zips):
    out = defaultdict(dict)
    for zipcode_id in tqdm(valid_zips):
        # Average Income
        avg_inc_df = load_csv("./data/avg_individual_income.csv", "ZIP code")
        avg_inc_df = avg_inc_df.set_index("ZIP code")
        average_income = avg_inc_df.loc[zipcode_id, "average income"]

        # Employment rate
        emp_rate_df = load_csv("./data/employment_rate.csv", "zipcode")
        emp_rate_df = emp_rate_df.set_index("zipcode")
        employment_rate = emp_rate_df.loc[zipcode_id, "employment rate"]

        # Population
        pop_df = load_csv("./data/population.csv", "zipcode")
        pop_df = pop_df.set_index("zipcode")
        population0_5 = int(pop_df.loc[zipcode_id, "-5"])
        population0_12 = int(pop_df.loc[zipcode_id, "-5"] + pop_df.loc[zipcode_id, "5-9"] + 3/5*(pop_df.loc[zipcode_id, "10-14"]))

        # Current existing childcare locations
        child_care_df = load_csv("./data/child_care_regulated.csv", "zip_code")
        child_care_rows = child_care_df[child_care_df["zip_code"] == zipcode_id].copy()
        # Handle empty names and Nonetype for locations (NaN values)
        num_cols = child_care_rows.select_dtypes(include=[np.number]).columns
        child_care_rows[num_cols] = child_care_rows[num_cols].fillna(0)
        obj_cols = child_care_rows.select_dtypes(include=["object"]).columns
        child_care_rows[obj_cols] = child_care_rows[obj_cols].fillna("")
        child_care_list = child_care_rows.to_dict(orient="records")
        child_care_dict = {entry["facility_id"]: entry for entry in child_care_list}

        # Potential childcare locations
        potent_care_df = load_csv("./data/potential_locations.csv", "zipcode")
        potent_care_rows = potent_care_df[potent_care_df["zipcode"] == zipcode_id]
        potent_care_list = potent_care_rows.to_dict(orient="records")

        # Combine data
        out[zipcode_id] = {
            "avg_individual_income": average_income,
            "employment_rate": employment_rate,
            "population0_5": population0_5,
            "population0_12": population0_12,
            "childcare_dict": child_care_dict,
            "potential_locations": potent_care_list
        }
    return out


'''
Main function
'''
if __name__ == "__main__":
    print(cf.bold(cf.seaGreen('Creating zipcode data...')))
    zipcode_intersection, length = find_zipcode_intersection()
    print(cf.bold(cf.seaGreen(f'Found {cf.yellow(length)} zipcodes existing in all 5 files')))
    filled = build_filled_zip_dict(zipcode_intersection)
    out_path = os.path.join(DATA_DIR, "zipcodes.json")
    with open(out_path, "w") as f:
        json.dump(filled, f, indent=2)
    print(cf.bold(cf.seaGreen('Completed successfully')))
    print(cf.bold(cf.seaGreen(f"Saved data to: {out_path}")))
