# Fake News Detector

Cloud-based application that analyzes news articles and identifies potentially
misleading or fabricated content using an ML text classifier plus heuristic
language-pattern analysis.

> **Disclaimer:** All results are automated model predictions based on
> statistical language patterns. They are **not proof** that a news story is
> false or true. Always verify claims with trusted primary sources.

## Architecture

```
React (Vite)  →  Flask API (Cloud Run)  →  TF-IDF + LogisticRegression model
                       │                            │
                       └── Firestore / SQLite  ←────┘   (prediction history + analytics)
```

- **Frontend** (`frontend/`): React + Vite. Analyze tab (text or article URL),
  History tab, Admin Dashboard tab (totals, label distribution, per-day chart).
- **Backend** (`backend/`): Flask API.
  - `POST /api/predict` — classify pasted text.
  - `POST /api/analyze-url` — fetch an article and classify its extracted text.
  - `GET /api/history`, `DELETE /api/history/<id>` — analysis history.
  - `GET /api/analytics` — dashboard aggregates.
  - `GET /api/health` — model/storage status.
- **Model** (`backend/train.py`): TF-IDF (1–2 grams) + LogisticRegression
  trained on a labeled `text,label` CSV (FAKE/REAL). Ships with a small
  placeholder dataset (`backend/data/sample_news.csv`) so it runs out of the
  box — for real accuracy, train on a large dataset such as
  [WELFake](https://github.com/KaiDMML/FakeNewsNet) (~72k articles).
- **Storage** (`backend/storage.py`): Google Cloud Firestore when
  `GOOGLE_CLOUD_PROJECT` is set, otherwise local SQLite — zero-config locally.

## Quick start (local)

```bash
# Backend
cd backend
pip install -r requirements.txt
python train.py            # trains on the bundled sample dataset
python app.py              # serves on http://localhost:5000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                # serves on http://localhost:5173 (proxies /api → :5000)
```

Train on your own dataset: `python train.py /path/to/dataset.csv`
(columns: `text,label`).

## Deploy to Google Cloud

### 1. Backend → Cloud Run + Firestore

```bash
cd backend
gcloud services enable run.googleapis.com firestore.googleapis.com

# Create a Firestore database (native mode) — skip if you keep local SQLite
gcloud firestore databases create --location=us-central

# Deploy; the image trains the model at build time
gcloud run deploy fake-news-api --source . --region=us-central \
  --set-env-vars GOOGLE_CLOUD_PROJECT=$(gcloud config get-value project) \
  --allow-unauthenticated
```

To train on a full dataset before deploying, put a `dataset.csv` in `backend/`
and change the Dockerfile's `RUN python train.py` step to
`RUN python train.py dataset.csv` (large builds may exceed Cloud Build limits —
pre-build with `python train.py` locally and copy `models/model.joblib` into
the image instead).

### 2. Frontend → Firebase Hosting / Cloud Storage

```bash
cd frontend
npm run build
# Point the app at the Cloud Run URL, then deploy:
API_TARGET=https://fake-news-api-xxx.run.app firebase deploy --only hosting
```

Or serve `frontend/dist` from Cloud Storage + Load Balancing, or deploy
the backend and frontend as two Cloud Run services with CORS (already enabled).

### 3. Optional: Vertex AI endpoint

To host the model on Vertex AI instead of in the container, export the
artifacts and create a custom prediction container, or use
`google-cloud-aiplatform` to call an AutoML/Vertex endpoint from
`model_service.py` and return the same response shape.

## Repository layout

```
backend/
  app.py            Flask API routes
  model_service.py  model loading + prediction
  patterns.py       suspicious-language heuristics
  storage.py        Firestore / SQLite adapter
  train.py          training script
  data/             dataset + local SQLite
  models/           trained artifact (generated)
  Dockerfile        Cloud Run image (trains at build time)
frontend/
  src/components/   Analyze, Result, History, Admin pages
```
