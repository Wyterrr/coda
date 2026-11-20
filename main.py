import os
import socket

import boto3
from fastapi import FastAPI, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine, text

from db_config import get_database_url
from predictor import predict_iris

DATABASE_URL = get_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL") or None
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY") or None
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY") or None
S3_BUCKET = os.environ["S3_BUCKET"]
S3_REGION = os.getenv("S3_REGION", "us-east-1")

s3_kwargs = {"region_name": S3_REGION}
if S3_ENDPOINT_URL:
    s3_kwargs["endpoint_url"] = S3_ENDPOINT_URL
if S3_ACCESS_KEY and S3_SECRET_KEY:
    s3_kwargs["aws_access_key_id"] = S3_ACCESS_KEY
    s3_kwargs["aws_secret_access_key"] = S3_SECRET_KEY

s3 = boto3.client("s3", **s3_kwargs)

app = FastAPI(title="CODA Monolith")


class Features(BaseModel):
    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        s3.head_bucket(Bucket=S3_BUCKET)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"status": "ready"}


@app.get("/info")
def info():
    return {
        "hostname": socket.gethostname(),
        "version": os.getenv("APP_VERSION", "cloud-ready"),
        "db": DATABASE_URL.split("@")[-1],
        "uploads": f"s3://{S3_BUCKET}",
    }


@app.post("/predict")
def predict(features: Features):
    values = [[features.sepal_length, features.sepal_width, features.petal_length, features.petal_width]]
    predicted = predict_iris(values[0])
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO predictions(features, predicted) VALUES (:features, :predicted)"),
            {"features": str(values[0]), "predicted": predicted},
        )
    return {"prediction": predicted, "hostname": socket.gethostname()}


@app.get("/predictions")
def predictions():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, features, predicted FROM predictions ORDER BY id")).fetchall()
    return [{"id": r[0], "features": r[1], "prediction": r[2]} for r in rows]


@app.post("/datasets")
async def upload_dataset(file: UploadFile = File(...)):
    content = await file.read()
    s3.put_object(Bucket=S3_BUCKET, Key=file.filename, Body=content)
    s3_path = f"s3://{S3_BUCKET}/{file.filename}"
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO datasets(name, path) VALUES (:name, :path)"),
            {"name": file.filename, "path": s3_path},
        )
    return {"name": file.filename, "path": s3_path, "hostname": socket.gethostname()}


@app.get("/datasets")
def datasets():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, name, path FROM datasets ORDER BY id")).fetchall()
    return [{"id": r[0], "name": r[1], "path": r[2]} for r in rows]
