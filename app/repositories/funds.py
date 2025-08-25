from db import db
from schema.funds import FundsOut
from bson import ObjectId

def get_funds() -> list[FundsOut]:
    """Obtiene todos los fondos disponibles.

    Returns:
        list[FundsOut]: Una lista de todos los fondos.
    """
    funds_cursor = db.funds.find()
    funds = [FundsOut(id = str(fund["fund_id"]), **fund) for fund in funds_cursor]
    return funds

def get_fund_by_id(fund_id: int) -> FundsOut | None:
    """
    Obtiene un fondo por su ID.

    Args:
        fund_id (int): El ID del fondo a recuperar.

    Returns:
        dict | None: Los detalles del fondo.
    """
    fund = db.funds.find_one({"fund_id": fund_id})
    if fund:
        return FundsOut(id = str(fund["fund_id"]), **fund)
    return None

def get_funds_by_category(category: str) -> list[FundsOut]:
    """ Obtiene fondos por categoría.

    Args:
        category (str): La categoría de fondos a recuperar.

    Returns:
        list[FundsOut]: Una lista de fondos de la categoría especificada.
    """
    funds_cursor = db.funds.find({"category": category})
    funds = [FundsOut(id = str(fund["fund_id"]), **fund) for fund in funds_cursor]
    return funds