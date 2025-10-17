import json
from gurobipy import Model, GRB, quicksum
import colorful as cf
import sys
from structs.zipcode import Zipcodes
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
Create optimization function
'''
def optimize(zipcodes: Zipcodes):
    # Sets
    I = zipcodes.get_complete_data()
    F = zipcodes.get_facilities()
    m = Model("childcare_deserts")

    # Decision variables
    x, u = {}, {}
    for i in I:
        for f in F[i]:
            x[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"x[{f}]")
            u[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"u[{f}]")
    y, v = {}, {}
    for i in I:
        for s in FACILITY_TYPES:
            y[i, s] = m.addVar(vtype=GRB.INTEGER, lb=0, name=f"y[{i},{s}]")
            v[i, s] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"v[{i},{s}]")
    x1, x2, x3 = {}, {}, {}
    for i in I:
        for f in F[i]:
            x1[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"x1[{f}]")
            x2[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"x2[{f}]")
            x3[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"x3[{f}]")
    m.update()

    # Constraints
    # Expansion limits: x_f <= min(1.2*Cap_f, 500)
    for i in I:
        for f in F[i]:
            cap = zipcodes.get_total_cap_for_facility(i, f)
            limit = min(1.2 * cap, 500)
            m.addConstr(x[f] <= limit, name=f"expansion_limit[{f}]")

    # Coverage: sum_f (Cap_f) + sum_f (x_f) + sum_s Cap_s*y_{i,s} >= theta_i * Pop_i
    for i in I:
        const_cap_sum = sum(zipcodes.get_total_cap_for_facility(i,f) for f in F[i]) 
        m.addConstr(
            const_cap_sum +
            quicksum(x[f] for f in F[i]) +
            quicksum(FACILITY_TYPES[s]["Cap"] * y[i, s] for s in FACILITY_TYPES)
            >= zipcodes.get_theta_for_zipcode(i) * zipcodes.get_population0_12_for_zipcode(i),
            name=f"coverage_zip[{i}]"
        )

    # 0–5 coverage: sum_f u_f + sum_s v_{i,s} >= (2/3)*Pop05_i
    for i in I:
        m.addConstr(
            quicksum(u[f] for f in F[i]) +
            quicksum(v[i, s] for s in FACILITY_TYPES)
            >= (2.0 / 3.0) * zipcodes.get_population0_5_for_zipcode(i),
            name=f"coverage_05_zip[{i}]"
        )

    # Consistency: 0 <= u_f <= x_f
    for i in I:
        for f in F[i]:
            m.addConstr(u[f] <= x[f], name=f"u_le_x[{f}]")

    for i in I:
        for f in F[i]:
            m.addConstr(x[f] == x1[f] + x2[f] + x3[f], name=f"tier_sum[{f}]")
    
    for i in I:
        for f in F[i]:
            n_f = zipcodes.get_total_cap_for_facility(i, f)
            m.addConstr(x1[f] <= 0.10 * n_f, name=f"tier1_cap[{f}]")
            m.addConstr(x2[f] <= 0.05 * n_f, name=f"tier2_cap[{f}]")
            m.addConstr(x3[f] <= 0.05 * n_f, name=f"tier3_cap[{f}]")
            # Optional hard cap for numerical safety:
            m.addConstr(x[f] <= 0.20 * n_f, name=f"expansion_20pct[{f}]")

    # Consistency: 0 <= v_{i,s} <= Cap05_s * y_{i,s}
    for i in I:
        for s in FACILITY_TYPES:
            m.addConstr(
                v[i, s] <= FACILITY_TYPES[s]["Cap05"] * y[i, s],
                name=f"v_cap[{i},{s}]"
            )
    

    # ---------- Objective ----------
    # Uses global DELTA, ALPHA, BETA, FACILITY_TYPES
    expansion_cost_terms = []
    for i in I:
        for f in F[i]:
            n_f = zipcodes.get_total_cap_for_facility(i, f)
            s1 = (20000.0 + 200.0  * n_f) / n_f
            s2 = (20000.0 + 400.0  * n_f) / n_f
            s3 = (20000.0 + 1000.0 * n_f) / n_f
            expansion_cost_terms.append(s1 * x1[f] + s2 * x2[f] + s3 * x3[f])

    expansion_cost = quicksum(expansion_cost_terms)
    new_build_cost = quicksum(FACILITY_TYPES[s]["Cost"] * y[i, s] for i in I for s in FACILITY_TYPES)

    new_build_cost = quicksum(FACILITY_TYPES[s]["Cost"] * y[i, s] for i in I for s in FACILITY_TYPES)
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

if __name__ == "__main__":
    in_path = sys.argv[1] 
    print(cf.bold(cf.seaGreen(f"Got zipcode data from: {cf.yellow(in_path)}")))
    with open(in_path, "r") as f:
        data = json.load(f)
    zipcodes = Zipcodes(data)
    print(cf.seaGreen("Begin optimizing..."))
    optimize(zipcodes)
    print(cf.seaGreen("Optimization complete"))
