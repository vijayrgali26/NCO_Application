import pandas as pd
from pathlib import Path
from utils import embed_texts, build_faiss_index, save_faiss

CSV_PATH = "occupations.csv"
MODEL_DIR = Path("models")
INDEX_PATH = MODEL_DIR / "occupations.index"
META_PATH = MODEL_DIR / "occupations_meta.parquet"

def prepare_text(row):
    return " . ".join([str(row[col]) for col in ["job_title", "description", "keywords"] if row[col]])

def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
    texts = [prepare_text(row) for _, row in df.iterrows()]
    embs = embed_texts(texts)
    index = build_faiss_index(embs)
    save_faiss(index, str(INDEX_PATH))
    df.reset_index(inplace=True)
    df.rename(columns={"index": "idx"}, inplace=True)
    df.to_parquet(META_PATH, index=False)
    print(f"Index and metadata saved to {MODEL_DIR}")

if __name__ == "__main__":
    main()
