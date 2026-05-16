# SHL Conversational Assessment Agent

FastAPI service for recommending SHL Individual Test Solutions from a scraped catalog.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python scripts\scrape_shl.py
uvicorn app.main:app --reload --port 8000
```

Open:

- Health: `http://localhost:8000/health`
- Chat: `POST http://localhost:8000/chat`

## Deploy

Deploy to Render/Railway/Fly/Hugging Face Spaces using:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
