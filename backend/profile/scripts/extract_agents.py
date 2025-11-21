import pandas as pd
import sys
import collections

# --------------------------------------------
# USAGE:
#   python extract_top10_agents.py <data-file>
# --------------------------------------------

if len(sys.argv) != 2:
    print("Usage: python extract_top10_agents.py <data-file>")
    sys.exit(1)

datafile = sys.argv[1]

# --------------------------------------------
# Load data file
# --------------------------------------------
try:
    df = pd.read_csv(datafile)
except:
    df = pd.read_csv(datafile, sep=",", engine="python")

# --------------------------------------------
# Extract all agents
# --------------------------------------------
agents = []

for _, row in df.iterrows():
    name_field = row.get("listingAgent.name")
    agency = row.get("agency.name")

    if pd.isna(name_field):
        continue

    # Handle multiple agents separated by commas
    for entry in str(name_field).split(","):
        entry = entry.strip()
        if not entry:
            continue

        parts = entry.split()
        first = parts[0]
        last = " ".join(parts[1:]) if len(parts) > 1 else ""

        agents.append((first, last, agency))

# --------------------------------------------
# Count agent appearances
# --------------------------------------------
counter = collections.Counter(agents)
top10 = counter.most_common(10)

# --------------------------------------------
# Output result
# --------------------------------------------
for ((first, last, agency), count) in top10:
    print(f"{count:<6} {first:<15} {last:<25} {agency}")

