"""Prediction history storage.

Uses Google Cloud Firestore when GOOGLE_CLOUD_PROJECT is set, otherwise a
local SQLite database so the app runs anywhere with zero setup.
"""
import json
import os
import sqlite3
import time
import uuid

USE_FIRESTORE = bool(os.environ.get("GOOGLE_CLOUD_PROJECT")) and not os.environ.get(
    "FORCE_LOCAL_STORAGE"
)
LOCAL_DB = os.path.join(os.path.dirname(__file__), "data", "predictions.db")

_firestore_client = None


def _get_firestore():
    global _firestore_client
    if _firestore_client is None:
        from google.cloud import firestore
        _firestore_client = firestore.Client()
    return _firestore_client


def _sqlite():
    os.makedirs(os.path.dirname(LOCAL_DB), exist_ok=True)
    conn = sqlite3.connect(LOCAL_DB)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY,
            created_at REAL,
            input_type TEXT,
            source_url TEXT,
            text_preview TEXT,
            label TEXT,
            confidence REAL,
            probabilities TEXT,
            patterns TEXT,
            model_version TEXT
        )
        """
    )
    return conn


def save_prediction(record):
    record = dict(record)
    record.setdefault("id", str(uuid.uuid4()))
    record.setdefault("created_at", time.time())

    if USE_FIRESTORE:
        doc = _get_firestore().collection("predictions").document(record["id"])
        doc.set(record)
        return record["id"]

    conn = _sqlite()
    conn.execute(
        """INSERT INTO predictions
           (id, created_at, input_type, source_url, text_preview, label,
            confidence, probabilities, patterns, model_version)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            record["id"], record["created_at"], record.get("input_type"),
            record.get("source_url"), record.get("text_preview"),
            record.get("label"), record.get("confidence"),
            json.dumps(record.get("probabilities")),
            json.dumps(record.get("patterns")),
            record.get("model_version"),
        ),
    )
    conn.commit()
    conn.close()
    return record["id"]


def list_predictions(limit=50, offset=0):
    if USE_FIRESTORE:
        docs = (
            _get_firestore()
            .collection("predictions")
            .order_by("created_at", direction="DESCENDING")
            .limit(limit)
            .offset(offset)
            .stream()
        )
        return [d.to_dict() for d in docs]

    conn = _sqlite()
    rows = conn.execute(
        "SELECT * FROM predictions ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    cols = [c[0] for c in conn.execute("SELECT * FROM predictions LIMIT 0").description]
    conn.close()
    out = []
    for row in rows:
        rec = dict(zip(cols, row))
        rec["probabilities"] = json.loads(rec["probabilities"] or "{}")
        rec["patterns"] = json.loads(rec["patterns"] or "[]")
        out.append(rec)
    return out


def delete_prediction(pred_id):
    if USE_FIRESTORE:
        _get_firestore().collection("predictions").document(pred_id).delete()
        return
    conn = _sqlite()
    conn.execute("DELETE FROM predictions WHERE id = ?", (pred_id,))
    conn.commit()
    conn.close()


def analytics():
    if USE_FIRESTORE:
        docs = [d.to_dict() for d in _get_firestore().collection("predictions").stream()]
        return _compute_analytics(docs)

    conn = _sqlite()
    rows = conn.execute(
        "SELECT created_at, label, confidence FROM predictions"
    ).fetchall()
    conn.close()
    return _compute_analytics(
        [{"created_at": r[0], "label": r[1], "confidence": r[2]} for r in rows]
    )


def _compute_analytics(records):
    total = len(records)
    by_label = {"FAKE": 0, "REAL": 0, "UNKNOWN": 0}
    conf_sum = 0.0
    by_day = {}
    for r in records:
        by_label[r.get("label", "UNKNOWN")] = by_label.get(r.get("label"), 0) + 1
        conf_sum += r.get("confidence") or 0.0
        day = time.strftime("%Y-%m-%d", time.localtime(r.get("created_at", 0)))
        by_day[day] = by_day.get(day, 0) + 1

    return {
        "total": total,
        "by_label": by_label,
        "avg_confidence": round(conf_sum / total, 4) if total else 0.0,
        "by_day": dict(sorted(by_day.items())),
        "storage": "firestore" if USE_FIRESTORE else "sqlite",
    }
