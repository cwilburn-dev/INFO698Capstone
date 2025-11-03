import random
import string
import csv

# parameters
start_year = 1880
end_year = 1914
num_bins = 7
entries_per_bin = 20

# bin sizing
year_range = end_year - start_year + 1
bin_size = year_range // num_bins
bins = []

# bin creation with letters
for i in range(num_bins):
    bin_start = start_year + i * bin_size
    bin_end = bin_start + bin_size - 1 if i < num_bins - 1 else end_year
    letters = [random.choice(string.ascii_uppercase) for _ in range(entries_per_bin)]
    bins.append({
        "bin": i + 1,
        "year_range": f"{bin_start}-{bin_end}",
        "letters": letters
    })

# results + csv creation
filename = "random-letters.csv"
with open(filename, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    # header
    header = ["Bin", "Year Range"] + [f"Letter {i+1}" for i in range(entries_per_bin)]
    writer.writerow(header)
    
    # data
    for b in bins:
        writer.writerow([b["bin"], b["year_range"]] + b["letters"])

print(f"Random letters written to '{filename}' successfully.")
