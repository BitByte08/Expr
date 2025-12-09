# utils/store.py
import chromadb
from chromadb.utils import embedding_functions
import os
from typing import Dict
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# 저장될 위치
PERSIST_DIR = os.getenv("CHROMA_PERSIST", "./chroma_db")

# 최신 Chroma 방식
client = chromadb.PersistentClient(path=PERSIST_DIR)

# 기본 embedding function (OPENAI/GEMINI도 붙일 수 있음)
embedder = embedding_functions.DefaultEmbeddingFunction()

# 컬렉션 생성
collection = client.get_or_create_collection(
    name="champion_info",
    embedding_function=embedder
)


def store_champion_data(champion: str, data: Dict[str, str], source: str):
    """
    data: dict[section] -> text
    """
    docs = []
    metadatas = []
    ids = []

    champion_lower = champion.lower()

    for section, text in data.items():
        if not text or len(text.strip()) < 10:
            continue

        doc_id = f"{champion_lower}::{section}::{source}"

        docs.append(text)
        metadatas.append({
            "champion": champion_lower,
            "section": section,
            "source": source
        })
        ids.append(doc_id)

    if docs:
        collection.add(documents=docs, metadatas=metadatas, ids=ids)
        logger.info(f"[Chroma] upserted {len(docs)} docs for {champion}")


def search_champion(champion: str, question: str, n_results: int = 3):
    """
    Returns Chroma result dict
    """
    champion_lower = champion.lower()
    query = f"{champion_lower} {question}"

    res = collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"champion": champion_lower}
    )

    return res
