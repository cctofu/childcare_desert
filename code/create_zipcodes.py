import colorful as cf
from collections import defaultdict
from tqdm import tqdm
import numpy as np
from utils import load_csv, normalize_zip
from structs.zipcode import Zipcodes
import sys
cf.use_style('monokai')

'''
Finds all NY zipcodes
'''
def find_zipcode_union(map):
    all_zips = set()
    for fname, zcol in map.items():
        df = load_csv(fname, zcol)
        for v in df[zcol].dropna().astype(str):
            nz = normalize_zip(v)
            all_zips.add(nz)
    return len(all_zips), all_zips


def get_income(zipcode_id):
    avg_inc_df = load_csv("./data/avg_individual_income.csv", "ZIP code")
    avg_inc_df = avg_inc_df.set_index("ZIP code")
    if zipcode_id in avg_inc_df.index:
        return avg_inc_df.at[zipcode_id, "average income"]
    else:
        return -1


def get_employment(zipcode_id):
    emp_rate_df = load_csv("./data/employment_rate.csv", "zipcode")
    emp_rate_df = emp_rate_df.set_index("zipcode")
    if zipcode_id in emp_rate_df.index:
        return emp_rate_df.at[zipcode_id, "employment rate"]
    else:
        return -1


def get_population(zipcode_id):
    pop_df = load_csv("./data/population.csv", "zipcode")
    pop_df = pop_df.set_index("zipcode")
    if zipcode_id in pop_df.index:
        population0_5 = int(pop_df.loc[zipcode_id, "-5"])
        population0_12 = int(pop_df.loc[zipcode_id, "-5"] + pop_df.loc[zipcode_id, "5-9"] + 3/5*(pop_df.loc[zipcode_id, "10-14"]))
        return population0_5, population0_12
    else:
        return (-1, -1)


def get_existing_childcare(zipcode_id):
    child_care_df = load_csv("./data/child_care_regulated.csv", "zip_code")
    child_care_df = child_care_df.set_index("zip_code")
    if zipcode_id in child_care_df.index:
        # Filter rows for this ZIP code
        child_care_rows = child_care_df.loc[[zipcode_id]].copy() 
        # Fill missing numeric and object values
        num_cols = child_care_rows.select_dtypes(include=[np.number]).columns
        child_care_rows[num_cols] = child_care_rows[num_cols].fillna(0)
        obj_cols = child_care_rows.select_dtypes(include=["object"]).columns
        child_care_rows[obj_cols] = child_care_rows[obj_cols].fillna("")
        # Convert to dict by facility_id
        child_care_list = child_care_rows.to_dict(orient="records")
        return {entry["facility_id"]: entry for entry in child_care_list}
    else:
        return {}


def get_potential_childcare(zipcode_id):
    potent_care_df = load_csv("./data/potential_locations.csv", "zipcode")
    potent_care_df = potent_care_df.set_index("zipcode")
    if zipcode_id in potent_care_df.index:
        potent_care_rows = potent_care_df.loc[[zipcode_id]].copy()
        potent_care_rows = potent_care_rows.fillna("")
        return potent_care_rows.to_dict(orient="records")
    else:
        return []


'''
Build dictionary with keys as zipcode values
'''
def build_filled_zip_dict(valid_zips):
    zipcodes = Zipcodes()
    for id in tqdm(valid_zips):
        # Average Income
        average_income = get_income(id)
        # Employment rate
        employment_rate = get_employment(id)
        # Population
        population0_5, population0_12 = get_population(id)
        # Current existing childcare locations
        child_care_dict = get_existing_childcare(id)
        # Potential childcare locations
        potent_care_list = get_potential_childcare(id)

        data = {
            "avg_individual_income": average_income,
            "employment_rate": employment_rate,
            "population0_5": population0_5,
            "population0_12": population0_12,
            "childcare_dict": child_care_dict,
            "potential_locations": potent_care_list,
        }
        zipcodes.add_zipcode(id, data)
    return zipcodes


if __name__ == "__main__":
    FILE_MAP= {
        "./data/avg_individual_income.csv": "ZIP code",
        "./data/child_care_regulated.csv": "zip_code",
        "./data/employment_rate.csv": "zipcode",
        "./data/population.csv": "zipcode",
        "./data/potential_locations.csv": "zipcode",
    }
    out_path = sys.argv[1] 
    print(cf.bold(cf.seaGreen('Creating zipcode data...')))
    length_union, all_zips = find_zipcode_union(FILE_MAP)
    print(cf.bold(cf.seaGreen(f'Found {cf.yellow(length_union)}/2158 zipcodes in total across all 5 files')))
    zipcodes = build_filled_zip_dict(all_zips)
    zipcodes.save_data_to_path(out_path)
    print(cf.bold(cf.seaGreen('Completed successfully')))
    print(cf.bold(cf.seaGreen(f"Saved data to: {cf.yellow(out_path)}")))
    zipcodes.print_summary()
