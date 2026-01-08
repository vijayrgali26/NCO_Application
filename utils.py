import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def embed_texts(texts):
    model = get_model()
    embs = model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
    return embs.astype('float32')

def build_faiss_index(embeddings):
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(embeddings)
    return index

def save_faiss(index, path):
    faiss.write_index(index, path)

def load_faiss(path):
    return faiss.read_index(path)

def top_k_search(index, query_emb, k=10):
    scores, ids = index.search(query_emb, k)
    return scores, ids
