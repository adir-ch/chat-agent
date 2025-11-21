import pandas as pd
import sys

# ---------------------------------------------
# USAGE:
#   python3 extract_listings.py <data-file> "First" "Last"
# ---------------------------------------------

if len(sys.argv) != 4:
    print("Usage: python3 extract_listings.py <data-file> <first-name> <last-name>")
    sys.exit(1)

datafile = sys.argv[1]
target_first = sys.argv[2].strip().lower()
target_last = sys.argv[3].strip().lower()

# ---------------------------------------------
# Load the dataset
# ---------------------------------------------
try:
    df = pd.read_csv(datafile)
except:
    df = pd.read_csv(datafile, sep=",", header=None, engine="python")

# ---------------------------------------------
# Detect agent column
# ---------------------------------------------
agent_col = None

# If a named column exists (structured report)
if "listingAgent.name" in df.columns:
    agent_col = "listingAgent.name"
else:
    # Raw report style (Camira, Bellbird Park, etc.)
    # Agent always appears in the **13th column**
    agent_col = 12  # index-based column

# ---------------------------------------------
# Extract listings for this agent
# ---------------------------------------------
records = []

for _, row in df.iterrows():

    # Get agent field (either named column or index)
    try:
        agent_field = row[agent_col]
    except:
        continue

    if pd.isna(agent_field):
        continue

    # Multiple agents may appear in one row
    agent_list = str(agent_field).split(",")

    for agent in agent_list:
        agent = agent.strip()
        if not agent:
            continue

        parts = agent.split()
        first = parts[0].lower()
        last = " ".join(parts[1:]).lower() if len(parts) > 1 else ""

        # Match requested agent
        if first == target_first and last == target_last:

            # Extract property data safely
            address = row.get("full_address", None)

            if not address:
                street_num = row.get("address.streetNumber", "")
                street_name = row.get("address.street", "")
                address = f"{street_num} {street_name}".strip()

            suburb = row.get("address.suburb.#text", "")
            postcode = row.get("address.postcode", "")
            status = row.get("@status", "")
            update = row.get("@modTime", "")

            records.append({
                "address": address,
                "suburb": suburb,
                "postcode": postcode,
                "status": status,
                "status_update": update
            })

# ---------------------------------------------
# Output results
# ---------------------------------------------
if not records:
    print(f"No listings found for agent: {target_first.capitalize()} {target_last.capitalize()}")
    sys.exit(0)

print(f"\nListings for: {target_first.capitalize()} {target_last.capitalize()}")
print("-------------------------------------------------------------")

for r in records:
    print(f"Address:       {r['address']}")
    print(f"Suburb:        {r['suburb']}")
    print(f"Postcode:      {r['postcode']}")
    print(f"Status:        {r['status']}")
    print(f"Updated:       {r['status_update']}")
    print("-------------------------------------------------------------")

print(f"\nTotal listings found: {len(records)}\n")
