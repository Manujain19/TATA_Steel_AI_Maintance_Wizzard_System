# Maintenance Wizard Deployment Guide

This project is a single FastAPI application. The backend APIs and the frontend in
`web/` are served by:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

## Recommended: Render Docker Deployment

1. Push this project to GitHub.

2. Go to Render and create a new **Blueprint** from the repository.

3. Render will detect `render.yaml`.

4. Add this secret environment variable in Render:

```text
GROQ_API_KEY=your_groq_key_here
```

5. Deploy.

6. Open the generated Render URL.

7. Verify:

```text
https://your-render-url/api/system-health
https://your-render-url/api/bootstrap
https://your-render-url/
```

## Manual Render Web Service

If you do not use the blueprint:

- Environment: Docker
- Dockerfile path: `Dockerfile`
- Health check path: `/api/system-health`

Environment variables:

```text
LLM_PROVIDER=groq
LLAMA_MODEL=llama-3.3-70b-versatile
GROQ_API_KEY=your_groq_key_here
VECTOR_DB=chromadb
CHROMA_PATH=/app/.vectorstores/chromadb
MODEL_MODE=download_if_missing
MODEL_CACHE_DIR=/app/.model_cache
ALLOW_MODEL_FALLBACK=true
AUTO_INDEX_VECTOR_STORE=true
BACKGROUND_PRELOAD=true
ENABLE_POSTGRES=false
EAGER_LOAD_AI_MODELS=false
ENABLE_RUNTIME_MODEL_LOADING=true
```

## Local Docker Test

```bash
docker build -t maintenance-wizard .
docker run --rm -p 8012:8012 --env-file .env maintenance-wizard
```

Open:

```text
http://127.0.0.1:8012
```

## VM Deployment

```bash
git clone <your-repository-url>
cd "Defect Detection in Hot Rolling"
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8012
```

Use Nginx or a cloud firewall to expose port `8012`.

## Production Notes

- The app can start without PostgreSQL because `ENABLE_POSTGRES=false` uses JSON
  seed data from `data/`.
- `AUTO_INDEX_VECTOR_STORE=true` allows ChromaDB to build the vector index on the
  deployed server if `.vectorstores/` is not included.
- `MODEL_MODE=download_if_missing` downloads Hugging Face models once when the
  container can access the internet.
- `ALLOW_MODEL_FALLBACK=true` keeps the demo available if the host blocks model
  downloads or has limited memory.
- For best quality, use a paid instance with enough memory for
  `sentence-transformers/all-MiniLM-L6-v2` and
  `cross-encoder/ms-marco-MiniLM-L-6-v2`.

## Demo Submission Links

After deployment, use:

```text
Demo Link: https://your-render-url
Health Check: https://your-render-url/api/system-health
```
