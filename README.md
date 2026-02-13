# Sentinel
Enterprise AI Operations Decision System
=======
Enterprise AI Operations Decision System with a working RAG pipeline.

## Status
- RAG ingestion endpoint: `POST /rag/ingest` reads markdown/text files from `backend/knowledge_base` and stores embeddings in `chroma_store`.
- Retrieval: decisions and evaluations pull top-K snippets from the KB for citations.

