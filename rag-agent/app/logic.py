import pandas as pd  # type: ignore
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from model import SearchResult
from intent_mapping import get_example_query


INDEX_PATH = "data/vd_index.faiss"
METADATA_PATH = "data/vd_metadata.csv"

model = SentenceTransformer("cointegrated/rubert-tiny2")
index = faiss.read_index(INDEX_PATH)
metadata = pd.read_csv(METADATA_PATH)


def get_answer_from_intent(intent: str) -> SearchResult:
    """
    Получает средний эмбеддинг по intent'у (одному или нескольким примерам),
    делает поиск ближайшего соседа в векторной БД и возвращает найденный ответ и источник.
    """
    queries = get_example_query(intent, mode="all")
    embeddings = model.encode(queries)
    mean_embedding = np.mean(embeddings, axis=0).reshape(1, -1)

    distances, indices = index.search(mean_embedding, 1)
    i = indices[0][0]
    row = metadata.iloc[i]

    return SearchResult(
        answer=row["correct_answer"],
        source=row["correct_sources"]
    )
