import json
from gurobipy import Model, GRB, quicksum
import colorful as cf
from structs.zipcode import Zipcode
cf.use_style('monokai')

'''
Preset values and variables
'''
FACILITY_TYPES = {
    "S": {"Cap": 100, "Cap05": 50,  "Cost": 65000},
    "M": {"Cap": 200, "Cap05": 100, "Cost": 95000},
    "L": {"Cap": 400, "Cap05": 200, "Cost": 115000},
}
ALPHA = 200     
BETA  = 100      
DELTA = 20000
EMPLOYMENT_THRESH = 0.60
INCOME_THRESH = 60000.0


'''
Load dataset
'''
def load_zip_data(path):
    with open(path, "r") as f:
        raw = json.load(f)
    zipcode_data = {zip_id: Zipcode(entry) for zip_id, entry in raw.items()}
    facilities = {}
    for z in zipcode_data:
        facilities[z] = zipcode_data[z].facility_ids
    return zipcode_data, facilities

'''
Create optimization function
'''
def build_and_solve(zipcode_data, facilities):
    # Sets
    I = sorted(zipcode_data.keys())
    F = facilities
    m = Model("childcare_deserts")

    # Decision variables
    x, u, z = {}, {}, {}
    for i in I:
        for f in F[i]:
            x[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"x[{f}]")
            u[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"u[{f}]")
            z[f] = m.addVar(vtype=GRB.BINARY, name=f"z[{f}]")
    y, v = {}, {}
    for i in I:
        for s in FACILITY_TYPES:
            y[i, s] = m.addVar(vtype=GRB.INTEGER, lb=0, name=f"y[{i},{s}]")
            v[i, s] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"v[{i},{s}]")
    m.update()

    # Constraints
    # Expansion limits: x_f <= min(0.2*Cap_f, 500)
    for i in I:
        for f in F[i]:
            cap = zipcode_data[i].get_total_capacity_for_id(f)
            limit = min(0.2 * cap, 500)
            m.addConstr(x[f] <= limit, name=f"expansion_limit[{f}]")

    # Coverage: sum_f (Cap_f) + sum_f (x_f) + sum_s Cap_s*y_{i,s} >= theta_i * Pop_i
    for i in I:
        const_cap_sum = sum(zipcode_data[i].get_total_capacity_for_id(f) for f in F[i]) 
        m.addConstr(
            const_cap_sum +
            quicksum(x[f] for f in F[i]) +
            quicksum(FACILITY_TYPES[s]["Cap"] * y[i, s] for s in FACILITY_TYPES)
            >= zipcode_data[i].theta * zipcode_data[i].population0_12,
            name=f"coverage_zip[{i}]"
        )

    # 0–5 coverage: sum_f u_f + sum_s v_{i,s} >= (2/3)*Pop05_i
    for i in I:
        m.addConstr(
            quicksum(u[f] for f in F[i]) +
            quicksum(v[i, s] for s in FACILITY_TYPES)
            >= (2.0 / 3.0) * zipcode_data[i].capacity0_5,
            name=f"coverage_05_zip[{i}]"
        )

    # Consistency: 0 <= u_f <= x_f
    for i in I:
        for f in F[i]:
            m.addConstr(u[f] <= x[f], name=f"u_le_x[{f}]")

    # Consistency: 0 <= v_{i,s} <= Cap05_s * y_{i,s}
    for i in I:
        for s in FACILITY_TYPES:
            m.addConstr(
                v[i, s] <= FACILITY_TYPES[s]["Cap05"] * y[i, s],
                name=f"v_cap[{i},{s}]"
            )

    # Binary trigger for baseline expansion cost: z_f indicates whether expansion reaches baseline cap
    for i in I:
        for f in F[i]:
            cap = zipcode_data[i].get_total_capacity_for_id(f)
            x_max = min(0.2 * cap, 500.0)
            M = x_max + cap
            m.addConstr(x[f] - cap <= M * z[f], name=f"trigger_up[{f}]")
            m.addConstr(x[f] - cap >= -M * (1 - z[f]), name=f"trigger_lo[{f}]")

    # ---------- Objective ----------
    # Uses global DELTA, ALPHA, BETA, FACILITY_TYPES
    expansion_cost = quicksum(
        (DELTA + 200.0 * zipcode_data[i].get_total_capacity_for_id(f)) * z[f] + ALPHA * x[f]
        for i in I for f in F[i]
    )

    new_build_cost = quicksum(
        FACILITY_TYPES[s]["Cost"] * y[i, s] for i in I for s in FACILITY_TYPES
    )

    equip_cost = BETA * (
        quicksum(u[f] for i in I for f in F[i]) +
        quicksum(v[i, s] for i in I for s in FACILITY_TYPES)
    )

    m.setObjective(expansion_cost + new_build_cost + equip_cost, GRB.MINIMIZE)
    m.optimize()

    
    status = m.Status
    if status in (GRB.OPTIMAL, GRB.INTERRUPTED, GRB.TIME_LIMIT, GRB.SUBOPTIMAL):
        print(cf.bold(cf.seaGreen("\n=== Solution summary ===")))
        if status == GRB.OPTIMAL:
            print(cf.seaGreen("Status: " + cf.yellow("OPTIMAL")))
        elif status == GRB.SUBOPTIMAL:
            print(cf.seaGreen("Status: " + cf.yellow("SUBOPTIMAL")))
        print(cf.seaGreen("Objective value: " + cf.bold(cf.yellow(f"${m.ObjVal:,.0f}"))))

        for i in I:
            f = F[i][0]
            exp_slots = x[f].X
            exp_05 = u[f].X
            trig = int(round(z[f].X))
            builds = {s: int(round(y[i, s].X)) for s in FACILITY_TYPES}
            v05 = {s: v[i, s].X for s in FACILITY_TYPES}

            # Uncomment to print only active actions
            # if (exp_slots > 1e-6) or any(builds[s] > 0 for s in FACILITY_TYPES):
            #     print(f"\nZIP {i}:")
            #     if exp_slots > 1e-6:
            #         print(f"  Expand existing facility by {exp_slots:.1f} slots"
            #               f" (0–5 slots in expansion: {exp_05:.1f}; trigger={trig})")
            #     for s in FACILITY_TYPES:
            #         if builds[s] > 0:
            #             print(f"  Build {builds[s]} × {s} ({FACILITY_TYPES[s]['Cap']} slots)"
            #                   f" with 0–5 slots assigned: {v05[s]:.1f}")


if __name__ == "__main__":
    path = "./data/zipcodes.json"
    print(cf.seaGreen("Begin optimizing..."))
    zipcodes, facilities = load_zip_data(path)
    build_and_solve(zipcodes, facilities)
    print(cf.seaGreen("Optimization complete"))
