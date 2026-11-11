"""Train the fake-news text classifier.

Usage:
    python train.py                     # trains on the bundled sample dataset
    python train.py path/to/dataset.csv # trains on your own labeled CSV

Expected CSV columns: text,label  (label: FAKE or REAL)

For meaningful accuracy, use a large labeled dataset such as WELFake
(~72k articles), LIAR, or FakeNewsNet. The bundled sample is only a
placeholder so the API runs out of the box.
"""
import csv
import os
import sys
import uuid

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

SAMPLE_CSV = os.path.join(os.path.dirname(__file__), "data", "sample_news.csv")
MODEL_DIR = os.path.join(os.path.dirname(__file__), "models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.joblib")


def load_dataset(path):
    texts, labels = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            text = (row.get("text") or "").strip()
            label = (row.get("label") or "").strip().upper()
            if text and label in ("FAKE", "REAL"):
                texts.append(text)
                labels.append(label)
    return texts, labels


def train(csv_path=SAMPLE_CSV):
    texts, labels = load_dataset(csv_path)
    if len(set(labels)) < 2:
        raise SystemExit("Dataset needs at least one FAKE and one REAL sample.")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    vectorizer = TfidfVectorizer(
        stop_words="english", ngram_range=(1, 2), max_features=50000,
        min_df=1,
    )
    clf = LogisticRegression(max_iter=1000, C=2.0)
    clf.fit(vectorizer.fit_transform(X_train), y_train)

    if X_test:
        acc = accuracy_score(y_test, clf.predict(vectorizer.transform(X_test)))
        print(f"Test accuracy: {acc:.3f} (on {len(X_test)} held-out samples)")
        print(classification_report(y_test, clf.predict(vectorizer.transform(X_test))))

    os.makedirs(MODEL_DIR, exist_ok=True)
    model_version = f"fake-news-lr-{uuid.uuid4().hex[:8]}"
    joblib.dump(
        {"vectorizer": vectorizer, "classifier": clf, "model_version": model_version},
        MODEL_PATH,
    )
    print(f"Saved model '{model_version}' to {MODEL_PATH}")


if __name__ == "__main__":
    train(sys.argv[1] if len(sys.argv) > 1 else SAMPLE_CSV)
