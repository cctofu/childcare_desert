import json
from gurobipy import Model, GRB, quicksum
import colorful as cf
import sys
from structs.zipcode import Zipcodes
import utils

cf.use_style('monokai')

# ---------- Constants ----------
FACILITY_TYPES = {
    "S": {"Cap": 100, "Cap05": 50,  "Cost": 65000},
    "M": {"Cap": 200, "Cap05": 100, "Cost": 95000},
    "L": {"Cap": 400, "Cap05": 200, "Cost": 115000},
}
ALPHA = 200
BETA  = 100
DELTA = 20000
DIST_LIMIT = 0.06

def optimize(zipcodes: Zipcodes, bin_size, plot_on, part2=False):
    # ---------- Sets ----------
    I = zipcodes.get_complete_data()
    F = zipcodes.get_facilities()

    m = Model("childcare_deserts")
    m.Params.OutputFlag = 0

    # ---------- Decision variables ----------
    x, u = {}, {}
    z, t1, t2, t3 = {}, {}, {}, {}

    for i in I:
        for f in F[i]:
            x[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"x[{f}]")
            u[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"u[{f}]")
            if not part2:
                z[f] = m.addVar(vtype=GRB.BINARY, name=f"z[{f}]")
            else:
                t1[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"t1[{f}]")
                t2[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"t2[{f}]")
                t3[f] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"t3[{f}]")

    # ---------- New facility variables ----------
    y, v, y_site, v_site = {}, {}, {}, {}
    if part2:
        for i in I:
            locs = zipcodes.data[i]["potential_locations"]
            for l in range(len(locs)):
                for s in FACILITY_TYPES:
                    y_site[i, l, s] = m.addVar(vtype=GRB.BINARY, name=f"y_site[{i},{l},{s}]")
                    v_site[i, l, s] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"v_site[{i},{l},{s}]")

        # aggregate to zipcode level
        for i in I:
            locs = zipcodes.data[i]["potential_locations"]
            for s in FACILITY_TYPES:
                y[i, s] = quicksum(y_site[i, l, s] for l in range(len(locs)))
                v[i, s] = quicksum(v_site[i, l, s] for l in range(len(locs)))

        # site constraints
        for i in I:
            locs = zipcodes.data[i]["potential_locations"]
            for l in range(len(locs)):
                m.addConstr(quicksum(y_site[i, l, s] for s in FACILITY_TYPES) <= 1)

        # distance rules
        for i in I:
            locs = zipcodes.data[i]["potential_locations"]
            for a in range(len(locs)):
                for b in range(a + 1, len(locs)):
                    d = zipcodes.get_site_distance(i, a, b)
                    if d < DIST_LIMIT:
                        m.addConstr(
                            quicksum(y_site[i, a, s] for s in FACILITY_TYPES) +
                            quicksum(y_site[i, b, s] for s in FACILITY_TYPES) <= 1
                        )

        # distance between potential sites and valid existing facilities
        for i in I:
            locs = zipcodes.data[i]["potential_locations"]
            for l in range(len(locs)):
                for f in F[i]:
                    d = zipcodes.get_distance_to_facility(i, l, f)
                    if d < DIST_LIMIT:
                        m.addConstr(quicksum(y_site[i, l, s] for s in FACILITY_TYPES) <= 1)
    else:
        for i in I:
            for s in FACILITY_TYPES:
                y[i, s] = m.addVar(vtype=GRB.INTEGER, lb=0, name=f"y[{i},{s}]")
                v[i, s] = m.addVar(lb=0.0, vtype=GRB.INTEGER, name=f"v[{i},{s}]")

    m.update()

    # ---------- Constraints ----------
    for i in I:
        for f in F[i]:
            cap = zipcodes.get_total_cap_for_facility(i, f)
            if part2:
                m.addConstr(x[f] <= 0.2 * cap)
                m.addConstr(x[f] == t1[f] + t2[f] + t3[f])
                m.addConstr(t1[f] <= 0.10 * cap)
                m.addConstr(t2[f] <= 0.05 * cap)
                m.addConstr(t3[f] <= 0.05 * cap)
            else:
                limit = min(1.2 * cap, 500)
                m.addConstr(x[f] <= limit)

    # Coverage + 0–5 coverage
    for i in I:
        base_cap = zipcodes.get_total_cap_for_zipcode(i)
        m.addConstr(
            base_cap +
            quicksum(x[f] for f in F[i]) +
            quicksum(FACILITY_TYPES[s]["Cap"] * y[i, s] for s in FACILITY_TYPES)
            >= zipcodes.get_theta_for_zipcode(i) * zipcodes.get_population0_12_for_zipcode(i)
        )
        m.addConstr(
            quicksum(u[f] for f in F[i]) +
            quicksum(v[i, s] for s in FACILITY_TYPES)
            >= (2/3) * zipcodes.get_population0_5_for_zipcode(i)
        )

    # Consistency
    for i in I:
        for f in F[i]:
            m.addConstr(u[f] <= x[f])
        for s in FACILITY_TYPES:
            m.addConstr(v[i, s] <= FACILITY_TYPES[s]["Cap05"] * y[i, s])

    # Binary trigger
    if not part2:
        for i in I:
            for f in F[i]:
                cap = zipcodes.get_total_cap_for_facility(i, f)
                x_max = min(1.2 * cap, 500.0)
                M = x_max + cap
                m.addConstr(x[f] - cap <= M * z[f])
                m.addConstr(x[f] - cap >= -M * (1 - z[f]))

    # ---------- Objective Function ----------
    new_build_cost = quicksum(FACILITY_TYPES[s]["Cost"] * y[i, s] for i in I for s in FACILITY_TYPES)
    equip_cost = BETA * (
        quicksum(u[f] for i in I for f in F[i]) +
        quicksum(v[i, s] for i in I for s in FACILITY_TYPES)
    )
    if part2:
        expansion_cost_terms = []
        for i in I:
            for f in F[i]:
                cap = zipcodes.get_total_cap_for_facility(i, f)
                coef_base = 20000.0 / cap
                expansion_cost_terms.append((200.0 + coef_base)  * t1[f])
                expansion_cost_terms.append((400.0 + coef_base)  * t2[f])
                expansion_cost_terms.append((1000.0 + coef_base) * t3[f])
        expansion_cost = quicksum(expansion_cost_terms)
    else:
        expansion_cost = quicksum(
            (DELTA + 200.0 * zipcodes.get_total_cap_for_facility(i, f)) * z[f] + ALPHA * x[f]
            for i in I for f in F[i]
        )
    m.setObjective(expansion_cost + new_build_cost + equip_cost, GRB.MINIMIZE)
    
    # ---------- Optimize ----------
    m.optimize()
    status = m.Status

    if status == GRB.OPTIMAL:
        if part2:
            print(cf.bold(cf.seaGreen("=== Part 2 Optimization summary ===")))
        else:
            print(cf.bold(cf.seaGreen("\n=== Part 1 Optimization summary ===")))
        print(cf.seaGreen("Status: " + cf.bold(cf.yellow("OPTIMAL"))))
        print(cf.seaGreen("Objective value: " + cf.bold(cf.yellow(f"${m.ObjVal:,.0f}"))))
        print("\n")
        if plot_on:
            utils.plot_x_expansion(x, F, bin_size, part2)
            utils.plot_u_expansion(u, bin_size, part2)
            utils.plot_cost_breakdown(m, expansion_cost, new_build_cost, equip_cost, part2)
            utils.plot_added_capacity_by_zip(zipcodes, x, y, FACILITY_TYPES, part2)
    else:
        print(cf.red("No feasible or optimal solution found."))

if __name__ == "__main__":
    in_path = sys.argv[1] 
    bin_size = sys.argv[2] 
    plot_on = sys.argv[3]

    # Fetch data
    print(cf.bold(cf.seaGreen(f"Got zipcode data from: {cf.yellow(in_path)}")))
    with open(in_path, "r") as f:
        data = json.load(f)
    zipcodes = Zipcodes(data)

    # Part 1 optimization
    optimize(zipcodes, bin_size, plot_on, part2=False)
    # Part 2 optimization
    optimize(zipcodes, bin_size, plot_on, part2=True)
