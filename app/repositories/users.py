from db import db
from schema.users import UserOut
from bson import ObjectId

DEFAULT_INITIAL_BALANCE = 500_000

def get_user_by_email(email: str) -> dict | None:
    """
    Obtiene un usuario de la base de datos por su correo electrónico.
    Args:
        email (str): El correo electrónico del usuario a buscar.

    Returns:
        dict | None: El documento del usuario si se encuentra, de lo contrario None.
    """
    return db.users.find_one({"email": email})

def get_user_by_cognito_id(cognito_id: str) -> dict | None:
    """
    Obtiene un usuario de la base de datos por su ID de Cognito.

    Args:
        cognito_id (str): El ID de Cognito del usuario a buscar.   
    
    Returns:
        dict | None: El documento del usuario si se encuentra, de lo contrario None.
    """
    user = db.users.find_one({"cognito_id": cognito_id})

    return UserOut(id=str(user["_id"]), **user) if user else None

def create_user(email: str, phone: str, cognito_id: str) -> UserOut:
    """
    Crea un nuevo usuario en la base de datos.

    Args:
        email (str): El correo electrónico del usuario.
        phone (str): El número de teléfono del usuario.
        cognito_id (str): El ID de Cognito del usuario.

    Returns:
        UserOut: El usuario creado.
    """

    user = get_user_by_email(email)
    if user:
        raise ValueError(f"User with email {email} already exists")

    user = {
        "email": email,
        "phone": phone,
        "balance": DEFAULT_INITIAL_BALANCE,
        "notif_options": "email",
        "cognito_id": cognito_id,
    }
    inserted_user = db.users.insert_one(user)
    final_user: UserOut = UserOut(id=str(inserted_user.inserted_id), **user)
    return final_user

def update_user_balance(user_id: str, new_balance: float) -> None:
    """
    Actualiza el balance de un usuario en la base de datos.
    
    Args:
        user_id (str): El ID del usuario a actualizar.
        new_balance (float): El nuevo balance del usuario.
    
    Returns:
        bool: True si la actualización fue exitosa, False en caso contrario.
    """
    user = db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return False
    db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"balance": new_balance}})
    return True

