from db import db
from schema.transactions import Transaction

def get_transactions(user_id: str) -> list[Transaction]:
    """
    Obtiene todas las transacciones asociadas a un usuario específico.

    Args:
        user_id (str): El ID del usuario para el cual se obtendrán las transacciones.

    Returns:
        list[Transaction]: Una lista de transacciones asociadas al usuario.
    """
    transactions = db.transactions.find({"user_id": user_id})
    return [Transaction(id = str(transaction["_id"]), **transaction) for transaction in transactions]

def create_transaction(transaction_data: dict) -> Transaction:
    """
    Crea una nueva transacción en la base de datos.

    Args:
        transaction_data (dict): Los datos de la transacción a crear.

    Returns:
        Transaction: La transacción creada
    """
    inserted_transaction = db.transactions.insert_one(transaction_data)
    transaction = db.transactions.find_one({"_id": inserted_transaction.inserted_id})
    return Transaction(id = str(transaction["_id"]), **transaction)

def get_transactions_by_user_and_fund(user_id: str, fund_id: str) -> list[Transaction]:
    """
    Obtiene todas las transacciones de un usuario para un fondo específico.

    Args:
        user_id (str): El ID del usuario.
        fund_id (str): El ID del fondo.

    Returns:
        list[Transaction]: Una lista de transacciones del usuario para el fondo especificado.
    """
    transactions = db.transactions.find({"user_id": user_id, "fund_id": fund_id})
    return [Transaction(id = str(transaction["_id"]), **transaction) for transaction in transactions]
