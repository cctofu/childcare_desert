EMPLOYMENT_THRESH = 0.60
INCOME_THRESH = 60000.0

class Zipcode:
    def __init__(self, entry):
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

    def get_total_capacity_for_id(self, facility_id):
        return self.childcare_dict[facility_id]["total_capacity"]
    
    def get_05_capacity_for_id(self, facility_id):
        return (self.childcare_dict[facility_id]["infant_capacity"] + 
                self.childcare_dict[facility_id]["toddler_capacity"] + 
                self.childcare_dict[facility_id]["preschool_capacity"])
    