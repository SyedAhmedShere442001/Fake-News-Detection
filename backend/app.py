"""Fake News Detector API.

Serves ML predictions, heuristic pattern analysis, URL article extraction,
and prediction history. Runs on Cloud Run or locally.
"""
import re
import time

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
from flask_cors import CORS

from model_service import ModelService
from patterns import analyze_patterns
import storage

app = Flask(__name__)
CORS(app)
model = ModelService()

MAX_TEXT_CHARS = 20000
MAX_FETCH_BYTES = 2 * 1024 * 1024
FETCH_TIMEOUT = 10
USER_AGENT = "FakeNewsDetectorBot/1.0 (research; contact: admin@example.com)"

URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _preview(text, n=280):
    text = " ".join(text.split())
    return text[:n] + ("..." if len(text) > n else "")


def _error(msg, status=400):
    return jsonify({"error": msg}), status


def _run_analysis(text, input_type, source_url=None):
    prediction = model.predict(text)
    findings = analyze_patterns(text)
    record = {
        "input_type": input_type,
        "source_url": source_url,
        "text_preview": _preview(text),
        "label": prediction["label"],
        "confidence": prediction["confidence"],
        "probabilities": prediction["probabilities"],
        "patterns": findings,
        "model_version": prediction["model_version"],
    }
    record["id"] = storage.save_prediction(record)
    return {**record, "inference_ms": prediction["inference_ms"], "disclaimer": prediction["disclaimer"]}


@app.get("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": model.is_ready(),
        "model_version": model.model_version,
        "storage": "firestore" if storage.USE_FIRESTORE else "sqlite",
        "time": time.time(),
    })


@app.post("/api/predict")
def predict():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return _error("Field 'text' is required and must not be empty.")
    if len(text) > MAX_TEXT_CHARS:
        return _error(f"Text exceeds the {MAX_TEXT_CHARS} character limit.")
    return jsonify(_run_analysis(text, input_type="text"))


@app.post("/api/analyze-url")
def analyze_url():
    body = request.get_json(silent=True) or {}
    url = (body.get("url") or "").strip()
    if not URL_RE.match(url):
        return _error("Only http:// and https:// URLs are supported.")

    try:
        resp = requests.get(
            url, timeout=FETCH_TIMEOUT, headers={"User-Agent": USER_AGENT},
            stream=True, allow_redirects=True,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        return _error(f"Could not fetch the article: {e.__class__.__name__}", 502)

    content_type = resp.headers.get("Content-Type", "")
    if "html" not in content_type and "text" not in content_type:
        resp.close()
        return _error(f"Unsupported content type: {content_type}", 415)

    chunks, size = [], 0
    for chunk in resp.iter_content(chunk_size=8192, decode_unicode=True):
        if not isinstance(chunk, str):
            chunk = chunk.decode("utf-8", errors="ignore")
        chunks.append(chunk)
        size += len(chunk)
        if size > MAX_FETCH_BYTES:
            break
    resp.close()

    soup = BeautifulSoup("".join(chunks), "lxml")
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
        tag.decompose()
    text = " ".join(soup.get_text(" ").split())
    if len(text) < 100:
        return _error("Could not extract enough article text from that page.", 422)

    return jsonify(_run_analysis(text[:MAX_TEXT_CHARS], input_type="url", source_url=url))


@app.get("/api/history")
def history():
    try:
        limit = min(int(request.args.get("limit", 50)), 200)
        offset = max(int(request.args.get("offset", 0)), 0)
    except ValueError:
        return _error("limit/offset must be integers.")
    return jsonify({"items": storage.list_predictions(limit=limit, offset=offset)})


@app.delete("/api/history/<pred_id>")
def delete_history(pred_id):
    storage.delete_prediction(pred_id)
    return jsonify({"deleted": pred_id})


@app.get("/api/analytics")
def analytics():
    return jsonify(storage.analytics())


if __name__ == "__main__":
    port = int(__import__("os").environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
