import os
from pymongo import MongoClient
from config import settings
from db import get_secret

def initialize_funds_collection():
    try:
        secret_string = get_secret()
        client = MongoClient(secret_string)
        db = client[settings.mongo_db]
        funds_collection = db.funds

        # Check if the collection is empty before inserting
        if funds_collection.count_documents({}) == 0:
            funds_data = [
                {"fund_id": 1, "Nombre": "FPV_BTG_PACTUAL_RECAUDADORA", "Monto_minimo": 75000, "Categoria": "FPV"},
                {"fund_id": 2, "Nombre": "FPV_BTG_PACTUAL_ECOPETROL", "Monto_minimo": 125000, "Categoria": "FPV"},
                {"fund_id": 3, "Nombre": "DEUDAPRIVADA", "Monto_minimo": 50000, "Categoria": "FIC"},
                {"fund_id": 4, "Nombre": "FDO-ACCIONES", "Monto_minimo": 250000, "Categoria": "FIC"},
                {"fund_id": 5, "Nombre": "FPV_BTG_PACTUAL_DINAMICA", "Monto_minimo": 100000, "Categoria": "FPV"}
            ]
            funds_collection.insert_many(funds_data)
            print("Funds collection initialized successfully.")
        else:
            print("Funds collection already contains data. Skipping initialization.")

    except Exception as e:
        print(f"Error initializing funds collection: {e}")

    finally:
        if 'client' in locals() and client:
            client.close()

if __name__ == "__main__":
    initialize_funds_collection()
