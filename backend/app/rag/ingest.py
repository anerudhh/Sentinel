import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


def ingest_kb(kb_dir: str, chroma_dir: str) -> int:
    if not os.path.isdir(kb_dir):
        raise RuntimeError(f"KB folder not found: {kb_dir}")

    docs = []
    for fn in os.listdir(kb_dir):
        if fn.endswith(".md") or fn.endswith(".txt"):
            path = os.path.join(kb_dir, fn)
            docs.extend(TextLoader(path, encoding="utf-8").load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n\n", "\n", ". ", " "],
    )
    chunks = splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    vectordb = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=chroma_dir,
        collection_name="sentinel_kb",
    )
    vectordb.persist()
    return len(chunks)
