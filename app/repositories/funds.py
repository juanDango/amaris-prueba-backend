from db import db
from schema.funds import FundsOut
from bson import ObjectId

def get_funds() -> list[FundsOut]:
    """Obtiene todos los fondos disponibles.

    Returns:
        list[FundsOut]: Una lista de todos los fondos.
    """
    funds_cursor = db.funds.find()
    funds = []
    print("funds: ", funds_cursor)
    for fund in funds_cursor:
        funds.append(FundsOut(id=str(fund["_id"]),**fund))
    return funds

def get_fund_by_id(fund_id: str) -> FundsOut | None:
    """
    Obtiene un fondo por su ID.

    Args:
        fund_id (int): El ID del fondo a recuperar.

    Returns:
        FundsOut | None: Los detalles del fondo.
    """
    obj_id = ObjectId(fund_id)
    fund = db.funds.find_one({"_id": obj_id})
    if fund:
        return FundsOut(id=str(fund["_id"]),**fund)
    return None

def get_funds_by_category(category: str) -> list[FundsOut]:
    """ Obtiene fondos por categoría.

    Args:
        category (str): La categoría de fondos a recuperar.

    Returns:
        list[FundsOut]: Una lista de fondos de la categoría especificada.
    """
    funds_cursor = db.funds.find({"category": category})
    funds = []
    for fund in funds_cursor:
        funds.append(FundsOut(id=str(fund["_id"]),**fund))
    return funds