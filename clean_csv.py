import pandas as pd

# Load the messy CSV
df = pd.read_csv("occupations.csv")

# Drop the "Unnamed: 0" column if it exists
if "Unnamed: 0" in df.columns:
    df = df.drop(columns=["Unnamed: 0"])

# Rule: Keep only rows where "Job Title" looks like a job (not metadata, introductions, etc.)
bad_keywords = [
    "Introduction", "Methodology", "Division", "Code Structure",
    "Educational", "NCO", "ISCO", "Occupational", "version",
    "International Labour Organization", "Globalization"
]

mask = df["Job Title"].apply(lambda x: not any(bad in str(x) for bad in bad_keywords))

df_clean = df[mask].copy().reset_index(drop=True)

# Save clean version
df_clean.to_csv("occupations_clean.csv", index=False)

print("✅ Saved occupations_clean.csv with", len(df_clean), "valid rows")
