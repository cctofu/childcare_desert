# Eliminating Child Care Deserts in New York State 

### Install dependencies 
Create conda environment and install dependencies
```
conda env create -f environment.yml
```
Put the 5 data files for the given problem in folder named `data`, this should create a structure that looks like:
```
childcare_desert/
│
├── code/
│   ├── structs/
│   ├── create_zipcodes.py
│   └── optimize.py
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

### Running Implementation
If all dependancies are installed correctly, first activate `conda` virtual env:
```
conda activate <your env name>
```
Then run the `.sh` file `run.sh`
```
bash ./run.sh
```

### Running Part of the Implementation
There are also two `.sh` files `preprocess.sh` and `optimize.sh` that run the code for their parts. 
```
bash ./preprocess.sh # Process data and fetch from api
bash ./optimize.sh # Run optimization on the given dataset json file
```
`optimize.sh` includes both the optimization for part 1 and optimization in part 2. The optimal values for each of the linear programs will be outputted and the graphs will be saved to the `./outputs` folder

If run correctly the result of the optimization should look something like:
```
Got zipcode data from: ./outputs/zipcodes_filled_1.json
=== Part 1 Optimization summary ===
Status: OPTIMAL
Objective value: $320,735,700

=== Part 2 Optimization summary ===
Status: OPTIMAL
Objective value: $511,744,910

```