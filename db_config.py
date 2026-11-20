import json
import os
from urllib.parse import quote_plus

import boto3


def get_database_url() -> str:
    """Return DATABASE_URL from env or build it from AWS Secrets Manager."""
    if os.getenv("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    secret_id = os.environ["DB_SECRET_NAME"]
    region = os.getenv("S3_REGION", os.getenv("AWS_REGION", "us-east-1"))
    client = boto3.client("secretsmanager", region_name=region)
    secret = json.loads(client.get_secret_value(SecretId=secret_id)["SecretString"])

    if "DATABASE_URL" in secret:
        return secret["DATABASE_URL"]

    user = quote_plus(secret["username"])
    password = quote_plus(secret["password"])
    host = secret["host"]
    port = secret.get("port", 5432)
    dbname = secret.get("dbname", "postgres")
    sslmode = secret.get("sslmode", "require")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode={sslmode}"
