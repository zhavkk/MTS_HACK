import os
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from pathlib import Path

DATA_PATH = Path("data/dataset.xlsx")
INDEX_PATH = Path("data/vd_index.faiss")
METADATA_PATH = Path("data/vd_metadata.csv")

MODEL_NAME = "cointegrated/rubert-tiny2"


def build_vector_database():
    """
    Преобразует датасет в векторную базу с помощью SentenceTransformer и сохраняет index + metadata.
    """
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Файл не найден: {DATA_PATH}")

    print(f"[INFO] Загрузка датасета из {DATA_PATH}")
    df = pd.read_excel(DATA_PATH)
    df = df[["query", "correct_answer", "correct_sources"]].dropna()

    print(f"[INFO] Загрузка модели эмбеддинга: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    print("[INFO] Генерация эмбеддингов...")
    queries = df["query"].tolist()
    embeddings = model.encode(queries, convert_to_numpy=True)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    os.makedirs("data", exist_ok=True)

    print(f"[INFO] Сохранение индекса в {INDEX_PATH}")
    faiss.write_index(index, str(INDEX_PATH))

    print(f"[INFO] Сохранение метаданных в {METADATA_PATH}")
    df.to_csv(METADATA_PATH, index=False)

    print("[SUCCESS] Векторная база успешно создана и сохранена.")


if __name__ == "__main__":
    build_vector_database()
