from collections import defaultdict
import json
import colorful as cf

class Zipcodes:
    def __init__(self, data=None):
        self.complete_data = set()
        self.missing_data = set()

        if data is None:
            self.data = {}
        else:
            self.data = data
            for key in self.data:
                if self.data[key].get('flag'):
                    self.missing_data.add(key)
                else:
                    self.complete_data.add(key)
    
    def add_zipcode(self, key, data):
        flag = 0
        if (data['avg_individual_income'] == -1 or 
            data['employment_rate'] == -1 or
            data['population0_5'] == -1 or 
            data['population0_12'] == -1 or 
            data['childcare_dict'] == {} or
            data['potential_locations'] == []):
            flag = 1
        data['flag'] = flag
        self.data[key] = data
        if flag == 1:
            self.missing_data.add(key)
        else:
            self.complete_data.add(key)

    def get_all_data_length(self):
        return len(self.data)

    def get_complete_data_length(self):
        return len(self.complete_data)
    
    def get_complete_data(self):
        return self.complete_data
    
    def get_facilities(self):
        facilities = {}
        for key in self.complete_data:
            facilities[key] = self.data[key]['childcare_dict']
        return facilities
    
    def get_total_cap_for_facility(self, key, facility):
        return self.data[key]['childcare_dict'][facility]['total_capacity']
    
    def get_infant_cap_for_facility(self, key, facility):
        return self.data[key]['childcare_dict'][facility]['infant_capacity']
    
    def get_theta_for_zipcode(self, key):
        EMPLOYMENT_THRESH = 0.60
        INCOME_THRESH = 60000.0
        if self.data[key]['employment_rate'] >= EMPLOYMENT_THRESH or self.data[key]['avg_individual_income'] <= INCOME_THRESH:
            return 0.5
        else:
            return (1.0 / 3.0)
    
    def get_population0_12_for_zipcode(self, key):
        return self.data[key]['population0_12']

    def get_population0_5_for_zipcode(self, key):
        return self.data[key]['population0_5']

    def get_missing_data_length(self):
        return len(self.missing_data)
    
    def get_missing_data(self):
        return list(self.missing_data)
    
    def get_missing_values(self, key):
        data = self.data[key]
        missing = []
        if data["avg_individual_income"] == -1:
            missing.append(0)
        if data["employment_rate"] == -1:
            missing.append(1)
        if data["population0_5"] == -1:
            missing.append(2)
        return missing
    
    def zipcode_is_complete(self, key):
        if self.data[key]['avg_individual_income'] == -1:
            return False
        if self.data[key]['employment_rate'] == -1:
            return False
        if self.data[key]['population0_5'] == -1:
            return False
        if self.data[key]['childcare_dict'] == {}:
            return False
        if self.data[key]['potential_locations'] == []:
            return False
        return True

    def modify_zipcode_values(self, key, data):
        for value in data:
            self.data[key][value] = data[value]
        if self.zipcode_is_complete(key):
            self.data[key]['flag'] = 0
            self.missing_data.remove(key)
            self.complete_data.add(key)
    
    def print_summary(self):
        def pct(x): 
            return 0.0 if total == 0 else 100.0 * x / total

        total = self.get_all_data_length()
        counts = defaultdict(int)
        for _, entry in self.data.items():
            # Read with defaults
            income = entry.get("avg_individual_income", -1)
            employment = entry.get("employment_rate", -1)
            pop05 = entry.get("population0_5", -1)
            pop012 = entry.get("population0_12", -1)
            childcare = entry.get("childcare_dict", {})
            potentials = entry.get("potential_locations", [])

            miss_income = income == -1
            miss_employment = employment == -1
            miss_pop5 = pop05 == -1
            miss_pop12 = pop012 == -1
            miss_childcare = (not isinstance(childcare, dict)) or (len(childcare) == 0)
            miss_potentials = (not isinstance(potentials, list)) or (len(potentials) == 0)

            if miss_income:
                counts["income"] += 1
            if miss_employment:
                counts["employment"] += 1
            if miss_pop5:
                counts["population0_5"] += 1
            if miss_pop12:
                counts["population0_12"] += 1
            if miss_childcare:
                counts["childcare_dict"] += 1
            if miss_potentials:
                counts["potential_locations"] += 1
    
        summary = {
            "missing_counts": {
                "income": counts["income"],
                "employment": counts["employment"],
                "population0_5": counts["population0_5"],
                "population0_12": counts["population0_12"],
                "childcare_dict": counts["childcare_dict"], 
                "potential_locations": counts["potential_locations"], 
            },
            "missing_percentages": {
                "income": pct(counts["income"]),
                "employment": pct(counts["employment"]),
                "population0_5": pct(counts["population0_5"]),
                "population0_12": pct(counts["population0_12"]),
                "childcare_dict": pct(counts["childcare_dict"]),
                "potential_locations": pct(counts["potential_locations"]),
            },
        }
        print(cf.bold(cf.seaGreen("===== ZIPCODE SUMMARY =====")))
        print(cf.seaGreen(f"Total entries: {total}"))
        print(cf.seaGreen(f"Entries with complete data: {self.get_complete_data_length()}"))
        print(cf.seaGreen(f"Entries with missing data: {self.get_missing_data_length()}"))
        print(cf.bold(cf.seaGreen("Missing Counts:")))
        for key, value in summary["missing_counts"].items():
            print(cf.yellow(f"  {key:<20}") + cf.bold(str(value)))
        print()
        print(cf.bold(cf.seaGreen("Missing Percentages:")))
        for key, value in summary["missing_percentages"].items():
            print(cf.yellow(f"  {key:<20}") + cf.bold(f"{value:.2f}%"))
        print(cf.bold(cf.seaGreen("============================")))


    def save_data_to_path(self, path):
        with open(path, "w") as f:
            json.dump(self.data, f, indent=2)
    
    '''CHANGES NEEDED
    def save_missing_to_path(self, path):
        with open(path, "w") as f:
            json.dump(self.missing_data, f, indent=2)
    
    def save_complete_to_path(self, path):
        with open(path, "w") as f:
            json.dump(self.complete_data, f, indent=2)
    '''

    '''
    def __init__(self, entry):
        EMPLOYMENT_THRESH = 0.60
    INCOME_THRESH = 60000.0
        self.population0_12 = entry.get("population0_12")
        self.population0_5 = entry.get("population0_5")
        income = float(entry.get("avg_individual_income"))
        employment_rate = float(entry.get("employment_rate"))

        if employment_rate >= EMPLOYMENT_THRESH or income <= INCOME_THRESH:
            self.theta = 0.5
        else:
            self.theta = (1.0 / 3.0)

        self.capacity0_12 = 0
        self.capacity0_5 = 0
        self.childcare_dict = entry.get("childcare_dict")
        self.facility_ids = []
        for f in self.childcare_dict:
            self.capacity0_12 += self.get_total_capacity_for_id(f)
            self.capacity0_5 += self.get_05_capacity_for_id(f)
            self.facility_ids.append(f)

        self.locations_list = entry.get("potential_locations")
    '''

    def get_total_capacity_for_id(self, facility_id):
        return self.childcare_dict[facility_id]["total_capacity"]
    
    def get_05_capacity_for_id(self, facility_id):
        return (self.childcare_dict[facility_id]["infant_capacity"] + 
                self.childcare_dict[facility_id]["toddler_capacity"] + 
                self.childcare_dict[facility_id]["preschool_capacity"])