FROM python:3.11-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV VECTOR_DB=chromadb
ENV CHROMA_PATH=/app/.vectorstores/chromadb
ENV MODEL_MODE=download_if_missing
ENV MODEL_CACHE_DIR=/app/.model_cache
ENV AUTO_INDEX_VECTOR_STORE=true
ENV ALLOW_MODEL_FALLBACK=true
ENV ENABLE_RUNTIME_MODEL_LOADING=true
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python scripts/build_vector_store.py --vector-db chromadb --embedding-model sentence-transformers/all-MiniLM-L6-v2 --real-model --force
EXPOSE 8012
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8012}"]
