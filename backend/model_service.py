"""Loads the trained classifier and exposes predict()."""
import os
import time

import joblib

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.joblib")

DISCLAIMER = (
    "This result is an automated model prediction based on statistical "
    "language patterns. It is NOT proof that a news story is false or true. "
    "Always verify claims with trusted primary sources."
)


class ModelService:
    def __init__(self, model_path=MODEL_PATH):
        self.model_path = model_path
        self.bundle = None
        self.model_version = "untrained"
        self._load()

    def _load(self):
        if os.path.exists(self.model_path):
            self.bundle = joblib.load(self.model_path)
            self.model_version = self.bundle.get("model_version", "unknown")
        # If no model artifact exists, predictions fall back to a neutral
        # response instead of crashing the API.

    def is_ready(self):
        return self.bundle is not None

    def predict(self, text):
        started = time.time()
        if not self.is_ready():
            return {
                "label": "UNKNOWN",
                "confidence": 0.0,
                "probabilities": {"FAKE": 0.5, "REAL": 0.5},
                "model_version": self.model_version,
                "inference_ms": round((time.time() - started) * 1000, 2),
                "disclaimer": DISCLAIMER,
            }

        vectorizer = self.bundle["vectorizer"]
        clf = self.bundle["classifier"]
        proba = clf.predict_proba(vectorizer.transform([text]))[0]
        classes = list(clf.classes_)
        fake_idx = classes.index("FAKE") if "FAKE" in classes else 0
        real_idx = classes.index("REAL") if "REAL" in classes else 1
        fake_p = float(proba[fake_idx])

        label = "FAKE" if fake_p >= 0.5 else "REAL"
        confidence = fake_p if label == "FAKE" else 1.0 - fake_p

        return {
            "label": label,
            "confidence": round(float(confidence), 4),
            "probabilities": {
                "FAKE": round(fake_p, 4),
                "REAL": round(1.0 - fake_p, 4),
            },
            "model_version": self.model_version,
            "inference_ms": round((time.time() - started) * 1000, 2),
            "disclaimer": DISCLAIMER,
        }
