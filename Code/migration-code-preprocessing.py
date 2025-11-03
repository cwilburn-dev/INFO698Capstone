import pandas as pd

# PRE-PROCESSING
# load and read dataset
file_path = "project-data-master.csv"
df = pd.read_csv(file_path)

# initial preview
print("Shape of dataset:", df.shape)
print("\nColumn names:", df.columns.tolist())
print("\nSample rows:")
print(df.head())

# convert ArrivalDate to datetime
if "ArrivalDate" in df.columns:
    def parse_dates(date_str):
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

# normalize ship names
if "ShipName" in df.columns:
    df["ShipName"] = df["ShipName"].str.replace(r'^(RMS|SS|MV|HMS)\s+', '', regex=True)

# maps name variants
ship_mapping = {
    "Augusta Victoria": "Kaiserin Augusta Victoria",
    "Kaiser Wilhelm II": "Kaiser Wilhelm II",
}
df['ShipName'] = df['ShipName'].replace(ship_mapping)

# normalize departure ports
if "DeparturePlace" in df.columns:
    # multiple departure ports
    df["TransitIndicator"] = df["DeparturePlace"].str.contains(" and ")
    # keep last port
    df["DeparturePlace"] = df["DeparturePlace"].str.split(" and ").str[-1].str.strip()

# summary
print("\nSummary by bin:")
print(df.groupby("Bin").size())

print("\nNumber of inferred multi-leg journeys (TransitIndicator=True):")
print(df["TransitIndicator"].sum())

# convert ArrivalDate back to "dd MMM yyyy" for csv
df['ArrivalDate'] = df['ArrivalDate'].dt.strftime('%d %b %Y')

# post-cleaning preview
print("Shape of dataset:", df.shape)
print("\nColumn names:", df.columns.tolist())
print("\nSample rows:")
print(df.head())

# cleaned csv
df.to_csv("migration_master_clean.csv", index=False)
print("\nCleaned data saved as migration_master_clean.csv")
