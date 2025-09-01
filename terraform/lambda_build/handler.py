import os
import base64
import boto3
import botocore
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

def get_secret(secret_id: str) -> str:
    cfg = botocore.config.Config(connect_timeout=10, read_timeout=10, retries={"max_attempts": 3})
    sm = boto3.client("secretsmanager", config=cfg)
    resp = sm.get_secret_value(SecretId=secret_id)
    if "SecretString" in resp:
        return resp["SecretString"]
    return base64.b64decode(resp["SecretBinary"]).decode("utf-8")

def lambda_handler(event, context):
    cluster_endpoint = event["cluster_endpoint"]
    secret_id        = event["secret_id"]
    db_name          = event.get("db_name", "amaris")
    username         = event.get("username", "amarisadmin")

    try:
        # Leer password del secret
        password = get_secret(secret_id)
    except Exception as e:
        return {"status": "error", "where": "secrets", "message": str(e)}

    # Ruta al bundle TLS empaquetado
    ca_path = os.path.join(os.path.dirname(__file__), "global-bundle.pem")
    if not os.path.exists(ca_path):
        return {"status":"error","where":"tls","message":f"No CA bundle at {ca_path}"}

    # Cadena de conexión con timeouts más largos
    mongo_uri = (
        f"mongodb://{username}:{password}@{cluster_endpoint}:27017/?tls=true&tlsCAFile={ca_path}&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
    )

    client = None
    try:
        client = MongoClient(
            mongo_uri,
            serverSelectionTimeoutMS=15000,  # Aumentado
            connectTimeoutMS=10000,          # Aumentado
            socketTimeoutMS=10000            # Aumentado
        )
        
        # Test de conexión
        client.admin.command("ping")
        
        db = client[db_name]
        coll = db["funds"]

        if coll.count_documents({}) > 0:
            return {"status": "ok", "message": "Funds collection already has data. Skipping."}

        funds_data = [
            {"fund_id": 1, "name": "FPV_BTG_PACTUAL_RECAUDADORA", "min_amount": 75000,  "category": "FPV"},
            {"fund_id": 2, "name": "FPV_BTG_PACTUAL_ECOPETROL",  "min_amount": 125000, "category": "FPV"},
            {"fund_id": 3, "name": "DEUDAPRIVADA",               "min_amount": 50000,  "category": "FIC"},
            {"fund_id": 4, "name": "FDO-ACCIONES",               "min_amount": 250000, "category": "FIC"},
            {"fund_id": 5, "name": "FPV_BTG_PACTUAL_DINAMICA",   "min_amount": 100000, "category": "FPV"},
        ]
        res = coll.insert_many(funds_data)
        return {"status": "ok", "message": f"Inserted {len(res.inserted_ids)} docs into '{db_name}.funds'"}

    except (ConnectionFailure, OperationFailure) as e:
        return {"status": "error", "where": "docdb", "message": str(e)}
    except Exception as e:
        return {"status": "error", "where": "general", "message": str(e)}
    finally:
        if client:
            client.close()
