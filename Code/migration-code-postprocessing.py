import pandas as pd

# POST PROCESSING CHECKS
# load clean dataset
file_path = "migration_master_clean.csv"
df = pd.read_csv(file_path)

# quick summary
print("Shape of dataset:", df.shape)
print("\nColumn names:", df.columns.tolist())
print("\nSample rows:")
print(df.head())

# descriptive stats for exploratory analysis
# counts by Bin, ArrivalYear, DeparturePlace, ShipName
print("\nNumber of records per bin:")
print(df.groupby("Bin").size())

print("\nNumber of records per year:")
print(df.groupby("ArrivalYear").size())

if "DeparturePlace" in df.columns:
    print("\nNumber of records per departure port:")
    print(df.groupby("DeparturePlace").size().sort_values(ascending=False))

if "ShipName" in df.columns:
    print("\nNumber of records per ship:")
    print(df.groupby("ShipName").size().sort_values(ascending=False))

# derived age
if "BirthDate" in df.columns:
    df["AgeAtArrival"] = df["ArrivalYear"] - df["BirthDate"]

print("\nSample with AgeAtArrival:")
print(df[["FirstName", "LastName", "BirthDate", "ArrivalYear", "AgeAtArrival"]].head())

# analysis-ready data csv
df.to_csv("migration_analysis_ready.csv", index=False)
print("\nAnalysis-ready dataset saved as migration_analysis_ready.csv")
