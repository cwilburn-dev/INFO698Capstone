import pandas as pd

# loads original data
file_path = "project-data-master.csv"
df = pd.read_csv(file_path)

print("Initial dataset loaded")
print("Shape:", df.shape)
print("Columns:", df.columns.tolist())
print("\nRaw Sample:")
print(df.head())

# date format corrections and derived ArrivalYear
if "ArrivalDate" in df.columns:
    def parse_dates(date_str):
        """Try multiple date formats until one matches."""
        for fmt in ("%d %b %Y", "%d-%b-%y", "%m/%d/%Y", "%m/%d/%y"):
            try:
                return pd.to_datetime(date_str, format=fmt)
            except (ValueError, TypeError):
                continue
        return pd.NaT

    df["ArrivalDate"] = df["ArrivalDate"].apply(parse_dates)
    df["ArrivalYear"] = df["ArrivalDate"].dt.year

# sort by ArrivalDate
if "ArrivalDate" in df.columns:
    df = df.sort_values(by="ArrivalDate")

# normalize ShipNames
if "ShipName" in df.columns:
    df["ShipName"] = df["ShipName"].str.replace(r'^(RMS|SS|MV|HMS)\s+', '', regex=True)

    # name mappings for variants
    ship_mapping = {
        "Augusta Victoria": "Kaiserin Augusta Victoria",
        "Kaiser Wilhelm II": "Kaiser Wilhelm II",
    }
    df["ShipName"] = df["ShipName"].replace(ship_mapping)

# departures
if "DeparturePlace" in df.columns:
    df["TransitIndicator"] = df["DeparturePlace"].str.contains(" and ", case=False, na=False)
    df["DeparturePlace"] = df["DeparturePlace"].str.split(" and ").str[-1].str.strip()

# derived AgeAtArrival
if "BirthDate" in df.columns:
    # Ensure numeric and handle invalid conversions
    df["BirthDate"] = pd.to_numeric(df["BirthDate"], errors="coerce")
    df["AgeAtArrival"] = df["ArrivalYear"] - df["BirthDate"]

# summaries
print("\nSummary by Bin:")
print(df.groupby("Bin").size())

if "DeparturePlace" in df.columns:
    print("\nTop Departure Ports:")
    print(df["DeparturePlace"].value_counts().head())

if "ShipName" in df.columns:
    print("\nTop Ships:")
    print(df["ShipName"].value_counts().head())

print("\nSample with computed age:")
print(df[["FirstName", "LastName", "BirthDate", "ArrivalYear", "AgeAtArrival"]].head())

# clean csv for data analysis
df.to_csv("migration_analysis_ready.csv", index=False)
print("\nAll steps complete — final file saved as migration_analysis_ready.csv")
