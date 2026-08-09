from langchain_experimental.text_splitter import SemanticChunker
from backend.rag.config import EMBEDDING_MODEL
from langchain_huggingface import HuggingFaceEmbeddings

embed=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

def split_documents(docs):
    splitter = SemanticChunker(embeddings=embed)
    return splitter.split_documents(docs)
