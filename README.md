# 🗽 Eliminating Child Care Deserts in New York State

### ⚙️ Install Dependencies

Create a new Conda environment and install all required packages:

```bash
conda env create -f environment.yml
```

Place the five required data files for the problem inside a folder named `data`.
Your project structure should look like this:

```
childcare_desert/
│
├── code/
│   ├── structs/
│   ├── create_zipcodes.py
│   └── optimize.py
│
└── data/
    ├── avg_individual_income.csv
    ├── child_care_regulated.csv
    ├── employment_rate.csv
    ├── expansions.csv
    ├── new_facilities.csv
    ├── population.csv
    ├── potential_locations.csv
    └── zip_coverage.csv
```

Create a `.env` file to store your U.S. Census API key in the following format:

```bash
API_KEY = "<Your key>"
```

---

### 🚀 Running the Implementation

After dependencies are installed, activate your Conda virtual environment:

```bash
conda activate <your_env_name>
```

Then simply run the main shell script:

```bash
bash ./run.sh
```

---

### 🧩 Running Individual Components

You can also run preprocessing and optimization separately using:

```bash
bash ./preprocess.sh   # 🧹 Process data and fetch from API
bash ./optimize.sh     # 🧮 Run optimization for Part 1 and Part 2
```

When executed successfully, the optimization will display output similar to:

```
Got zipcode data from: ./outputs/zipcodes_filled_1.json
=== Part 1 Optimization summary ===
Status: OPTIMAL
Objective value: $320,735,700

=== Part 2 Optimization summary ===
Status: OPTIMAL
Objective value: $511,744,910
```

Graphs and results will be automatically saved in the `./outputs` folder 📊.

---

### 🗺️ Visualizing the Map

To visualize ZIP-level childcare coverage on a map:

1. Visit the Census Bureau website:
   👉 [https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html](https://www.census.gov/geographies/mapping-files/time-series/geo/carto-boundary-file.html)
2. Download the **ZIP Code Tabulation Areas (ZCTAs)** file.
3. Create a new folder `./extra_data` and move the downloaded file there.
4. Run the mapping script:

   ```bash
   bash ./map_zips.sh
   ```

Visualizations will then appear in the `./outputs` directory.
