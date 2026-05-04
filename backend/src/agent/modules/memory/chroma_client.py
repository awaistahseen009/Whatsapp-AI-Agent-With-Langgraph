import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from config import Config

_embeddings = None
_chroma_client = None


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=Config.OPENAI_API_KEY
        )
    return _embeddings


def _get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.HttpClient(
            host=Config.CHROMA_HOST,
            port=Config.CHROMA_PORT
        )
    return _chroma_client


def get_collection(collection_name: str) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        embedding_function=get_embeddings(),
        client=_get_chroma_client()
    )