# Eliminating Child Care Deserts in New York State

### Install dependencies
Create conda environment and install dependencies
```
conda env create -f environment.yml
```
Put following data files in folder named `data`
Structure should look like:
```
childcare_desert/
│
├── code/
│   ├── main.py
│   ├── utils.py
│   └── __init__.py
│
└──data/
    ├── avg_individual_income.csv
    ├── child_care_regulated.csv
    ├── employment_rate.csv
    ├── expansions.csv
    ├── new_facilities.csv
    ├── population.csv
    ├── potential_locations.csv
    └── zip_coverage.csv
```

### Constructing Zipcode data
Then create zipcode dataset using command:
```
python ./code/create_zipcodes.py
```
This should create a file `zipcode.json` in the `./data` file.

### Running optimization
Finally, run optimization based on parameters and constraints listed:
```
python ./code/optimize.py
```
The outputted results is the optimal solution for the given problem