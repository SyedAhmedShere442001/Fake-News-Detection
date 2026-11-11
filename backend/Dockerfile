# Cloud Run image: trains the model at build time if no prebuilt artifact
# is copied in, then serves the Flask API.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Train the model during the image build so the artifact ships with the
# container. Set DATASET_CSV to build args to train on a full dataset.
RUN python train.py

CMD ["python", "app.py"]
