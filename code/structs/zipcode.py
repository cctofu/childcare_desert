from collections import defaultdict
import json
import colorful as cf
import math

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
    
    def get_children_cap_for_facility(self, key, facility):
        return self.data[key]['childcare_dict'][facility]['total_capacity']
    
    def get_children_cap_for_zipcode(self, key):
        total = 0
        for f in self.data[key]['childcare_dict']:
            total += self.data[key]['childcare_dict'][f]['total_capacity']
        return total
    
    def get_children_population_for_zipcode(self, key):
        return self.data[key]['population0_12']

    def get_infant_population_for_zipcode(self, key):
        return self.data[key]['population0_5']
    
    def get_infant_cap_for_zipcode(self, key):
        total = 0
        for f in self.data[key]['childcare_dict']:
            total += self.data[key]['childcare_dict'][f]['infant_capacity']
        return total
    
    def get_infant_cap_for_facility(self, key, facility):
        return self.data[key]['childcare_dict'][facility]['infant_capacity']
    
    def get_theta_for_zipcode(self, key):
        EMPLOYMENT_THRESH = 0.60
        INCOME_THRESH = 60000.0
        if self.data[key]['employment_rate'] >= EMPLOYMENT_THRESH or self.data[key]['avg_individual_income'] <= INCOME_THRESH:
            return 0.5
        else:
            return (1.0 / 3.0)

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
    
    def save_data_to_path(self, path):
        with open(path, "w") as f:
            json.dump(self.data, f, indent=2)

    def _haversine_miles(self, lat1, lon1, lat2, lon2):
        R = 3958.8 
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def get_site_distance(self, zipcode, site1, site2):
        locs = self.data[zipcode]["potential_locations"]
        lat1, lon1 = locs[site1]["latitude"], locs[site1]["longitude"]
        lat2, lon2 = locs[site2]["latitude"], locs[site2]["longitude"]
        return self._haversine_miles(lat1, lon1, lat2, lon2)

    def get_distance_to_facility(self, zipcode, site_idx, facility_id):
        loc = self.data[zipcode]["potential_locations"][site_idx]
        fac = self.data[zipcode]["childcare_dict"][facility_id]
        return self._haversine_miles(
            loc["latitude"], loc["longitude"],
            fac["latitude"], fac["longitude"]
        )

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
        