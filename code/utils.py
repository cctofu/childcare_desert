import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os
import colorful as cf

'''
Ensure zipcode is 5 digits, trim to 5 if longer than 5
'''
def normalize_zip(z):
    """
    Ensure ZIP is a 5-digit string, preserving leading zeros.
    """
    s = str(z).strip()
    if not s:
        return None
    if len(s) > 5:
        s = s[:5]
    if s.isdigit() and len(s) < 5:
        s = s.zfill(5)
    return s


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
Plot distribution for average expansion in zipcode
'''
def plot_x_expansion(x, F, bin_size, part2, save_dir="./outputs"):
    avg_expansions = []
    zero_count = 0

    for i in F:
        expansions = [x[f].X for f in F[i]]
        if all(abs(val) < 1e-6 for val in expansions): 
            zero_count += 1
        else:
            avg_expansion = sum(expansions) / len(expansions)
            if avg_expansion > 1e-6:
                avg_expansions.append(avg_expansion)

    max_val = max(avg_expansions) if avg_expansions else 0
    bins = np.arange(1, max_val + bin_size, bin_size)  
    labels = [f"{int(b)}–{int(b + bin_size - 1)}" for b in bins[:-1]]

    df = pd.DataFrame({"avg_expansion": avg_expansions})
    df["bin"] = pd.cut(df["avg_expansion"], bins=bins, labels=labels, include_lowest=True)
    grouped = df["bin"].value_counts().sort_index()
    grouped = pd.concat([pd.Series({"0": zero_count}), grouped])

    plt.figure(figsize=(10, 7))
    sns.barplot(x=grouped.index, y=grouped.values, color="seagreen")
    plt.title("Average Expansion per Zipcode", fontsize=15, fontweight="bold")
    plt.xlabel("Average Expansion Range (slots)", fontsize=12)
    plt.ylabel("Number of Zipcodes", fontsize=12)
    plt.xticks(rotation=45, ha="right")

    for idx, value in enumerate(grouped.values):
        plt.text(idx, value + max(grouped.values) * 0.01, str(int(value)),
                 ha='center', va='bottom', fontsize=10, color='black', fontweight='medium')

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    if part2:
        save_path = os.path.join(save_dir, "avg_expansion_2.png")
    else:
        save_path = os.path.join(save_dir, "avg_expansion_1.png")
    plt.savefig(save_path, dpi=300)
    plt.close()


'''
Plot distribution for average age 0 - 5 expansion in zipcode
'''
def plot_u_expansion(u, bin_size, part2, save_dir="./outputs"):
    u_values = [var.X for var in u.values()]
    zero_count = sum(1 for val in u_values if abs(val) < 1e-6)
    u_values = [val for val in u_values if val > 1e-6]

    max_val = max(u_values) if u_values else 0
    bins = np.arange(1, max_val + bin_size, bin_size)  # start from 1
    labels = [f"{int(b)}–{int(b + bin_size - 1)}" for b in bins[:-1]]

    df = pd.DataFrame({"u_value": u_values})
    df["bin"] = pd.cut(df["u_value"], bins=bins, labels=labels, include_lowest=True)
    grouped = df["bin"].value_counts().sort_index()
    grouped = pd.concat([pd.Series({"0": zero_count}), grouped])

    plt.figure(figsize=(10, 7))
    sns.barplot(x=grouped.index, y=grouped.values, color="seagreen")
    plt.title("0–5 Expansion Slots per Facility", fontsize=15, fontweight="bold")
    plt.xlabel("0–5 Expansion Range (slots)", fontsize=12)
    plt.ylabel("Number of Facilities", fontsize=12)
    plt.xticks(rotation=45, ha="right")

    for idx, value in enumerate(grouped.values):
        plt.text(idx, value + max(grouped.values) * 0.01, str(int(value)),
                 ha='center', va='bottom', fontsize=10, color='black', fontweight='medium')

    plt.tight_layout()
    os.makedirs(save_dir, exist_ok=True)
    if part2:
        save_path = os.path.join(save_dir, "u_expansion_2.png")
    else:
        save_path = os.path.join(save_dir, "u_expansion_1.png")
    plt.savefig(save_path, dpi=300)
    plt.close()


'''
Cost breakdown for the optimal budget
'''
def plot_cost_breakdown(m, expansion_cost, new_build_cost, equip_cost, part2, save_dir="./outputs"):
    import os
    import pandas as pd
    import seaborn as sns
    import matplotlib.pyplot as plt

    os.makedirs(save_dir, exist_ok=True)
    df = pd.DataFrame({
        "Category": ["Expansion", "New Builds", "Equipment"],
        "Cost": [expansion_cost.getValue(), new_build_cost.getValue(), equip_cost.getValue()]
    })

    plt.figure(figsize=(10, 7))
    ax = sns.barplot(
        data=df, x="Category", y="Cost",
        hue="Category", palette="viridis", legend=False
    )
    ax.margins(y=0.2)
    plt.title(f"Cost Breakdown — {'Part 2' if part2 else 'Part 1'}",
              fontsize=14, fontweight="bold")
    plt.ylabel("Cost ($)")
    plt.xticks(rotation=15)
    for idx, val in enumerate(df["Cost"]):
        plt.text(idx, val + 0.02 * df["Cost"].max(),
                 f"${val/1e6:.2f} M", ha="center", va="bottom",
                 fontsize=10, fontweight="medium")

    plt.tight_layout(pad=2)
    save_path = os.path.join(save_dir, f"cost_breakdown_{'part2' if part2 else 'part1'}.png")
    plt.savefig(save_path, dpi=300)
    plt.close()


"""
Plot newly added and expanded slots by ZIP code.
"""
def plot_added_capacity_by_zip(zipcodes, x, y, FACILITY_TYPES, part2):
    if part2:
        save_path="./outputs/added_capacity_by_zip_2.png"
    else:
        save_path="./outputs/added_capacity_by_zip_1.png"
    zip_list = sorted(list(zipcodes.get_complete_data()))
    expanded_slots, new_slots = [], []

    for i in zip_list:
        exp_sum = 0.0
        for f in zipcodes.data[i]["childcare_dict"]:
            val = x.get(f, 0)
            try:
                exp_sum += float(val.X)
            except AttributeError:
                exp_sum += float(val)
        expanded_slots.append(exp_sum)

        new_sum = 0.0
        for s in ["S", "M", "L"]:
            key = (i, s)
            if key in y:
                val = y[key]
                try:
                    numeric_val = float(val.X)
                except AttributeError:
                    try:
                        numeric_val = float(val.getValue()) 
                    except Exception:
                        numeric_val = 0.0
                new_sum += numeric_val * FACILITY_TYPES[s]["Cap"]
        new_slots.append(new_sum)

    indices = np.arange(len(zip_list))
    bar_width = 0.4
    plt.figure(figsize=(12, 6))
    plt.bar(indices - bar_width/2, expanded_slots, bar_width, label="Expanded Slots", color="#2E86C1")
    plt.bar(indices + bar_width/2, new_slots, bar_width, label="New Slots", color="#E67E22")

    tick_positions = indices[::35]
    tick_labels = [zip_list[i] for i in range(0, len(zip_list), 35)]
    plt.xticks(tick_positions, tick_labels, rotation=90, fontsize=8)
    plt.title("Newly Added and Expanded Slots by ZIP Code", fontsize=14, weight="bold")
    plt.xlabel("ZIP Code", fontsize=12)
    plt.ylabel("Number of Slots", fontsize=12)
    plt.legend()
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

