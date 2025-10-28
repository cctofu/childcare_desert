'''
UTILITY FUNCTIONS
'''
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import os


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
    # If it's longer than 5 (e.g., ZIP+4), truncate to 5
    if len(s) > 5:
        s = s[:5]
    # Zero-pad if numeric and shorter than 5
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
        if all(abs(val) < 1e-6 for val in expansions):  # all zero
            zero_count += 1
        else:
            avg_expansion = sum(expansions) / len(expansions)
            if avg_expansion > 1e-6:
                avg_expansions.append(avg_expansion)

    max_val = max(avg_expansions) if avg_expansions else 0
    bins = np.arange(1, max_val + bin_size, bin_size)  # start from 1
    labels = [f"{int(b)}–{int(b + bin_size - 1)}" for b in bins[:-1]]

    df = pd.DataFrame({"avg_expansion": avg_expansions})
    df["bin"] = pd.cut(df["avg_expansion"], bins=bins, labels=labels, include_lowest=True)
    grouped = df["bin"].value_counts().sort_index()

    # prepend separate zero bin
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

    # prepend separate zero bin
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