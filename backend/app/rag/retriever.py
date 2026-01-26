from typing import List, Dict
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma


def retrieve_context(query: str, chroma_dir: str, k: int = 4) -> List[Dict]:
    vectordb = Chroma(
        collection_name="sentinel_kb",
        embedding_function=OpenAIEmbeddings(),
        persist_directory=chroma_dir,
    )

    docs = vectordb.similarity_search(query, k=k)

    ctx = []
    for i, d in enumerate(docs, start=1):
        source = (d.metadata.get("source") or "unknown").split("/")[-1]
        ctx.append(
            {
                "id": f"S{i}",
                "source": source,
                "text": d.page_content,
            }
        )
    return ctx
