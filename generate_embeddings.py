import pandas as pd
from sentence_transformers import SentenceTransformer
import ast

# Load CSV
df = pd.read_csv("occupations_clean.csv")

# Keep only rows with valid job titles
df = df.dropna(subset=["Job Title"])

# Load model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Generate embeddings
print("🔄 Generating embeddings...")
df["embeddings"] = df["Job Title"].apply(lambda x: model.encode(x).tolist())

# Save to a new CSV with embeddings
df.to_csv("occupations_with_embeddings.csv", index=False)
print("✅ Saved occupations_with_embeddings.csv with embeddings")
