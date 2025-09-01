from fastapi import APIRouter, HTTPException, Depends
from bson.errors import InvalidId

from repositories.funds import get_fund_by_id, get_funds_by_category, get_funds
from repositories.users import get_user_by_cognito_id, update_user_balance
from repositories.transactions import get_transactions, create_transaction,  get_transactions_by_user_and_fund
from schema.funds import FundsCategories, FundsOut
from schema.users import UserOut, NotificationOptions
from schema.transactions import TransactionType, TransactionIn, Transaction
from datetime import datetime, timezone
from bson import ObjectId
from notifications import EmailNotifier, Message, SMSNotifier

from security.auth import get_current_user

email_notifier = EmailNotifier()
sms_notifier = SMSNotifier()

router = APIRouter(prefix="/funds", tags=["funds"])


@router.get("/{fund_id}", response_model=FundsOut)
async def read_fund(fund_id: str):
    """Obtiene un fondo por su ID.

    Args:
        fund_id (int): El ID del fondo a recuperar.

    Returns:
        FundsOut: Los detalles del fondo.
    """
    fund = get_fund_by_id(fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    return fund
    
@router.get("/category/{category}")
async def read_funds_by_category(category: FundsCategories):   
    """Obtiene fondos por categoría.

    Args:
        category (FundsCategories): La categoría de fondos a recuperar.

    Returns:
        list: Una lista de fondos de la categoría especificada.
    """
    funds = get_funds_by_category(category.value)
    return funds


@router.get("/", response_model=list[FundsOut])
async def read_all_funds():
    """Obtiene todos los fondos disponibles.   
    Returns:
        list: Una lista de todos los fondos.
    """
    funds = get_funds()
    return funds


@router.get("/get/transactions")
async def read_transactions_by_user(current_user: dict = Depends(get_current_user)):
    """Obtiene todas las transacciones asociadas al usuario autenticado.

    Args:
        current_user (dict): El usuario autenticado, inyectado por dependencia. 

    Returns:
        list: Una lista de transacciones del usuario.
    """
    cognito_user_id = current_user["sub"]

    user = get_user_by_cognito_id(cognito_user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = get_transactions(user_id=user.id)
    return transactions




@router.post("/post/transactions", response_model=Transaction)
async def create_transactions(
    transaction_in: TransactionIn,
    current_user: dict = Depends(get_current_user)
):
    """Crea una nueva transacción para el usuario autenticado.

    Args:
        transaction_in (TransactionIn): Los detalles de la transacción a crear.
        current_user (dict): El usuario autenticado, inyectado por dependencia.

    Returns:
        Transaction: La transacción creada.
    """

    # Verificar el usuario autenticado
    cognito_user_id = current_user["sub"]
    user: UserOut | None = get_user_by_cognito_id(cognito_user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Verificar que el fondo existe
    fund = get_fund_by_id(transaction_in.fund_id)
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")

    # Obtener todas las transacciones del usuario para este fondo
    fund_transactions = get_transactions_by_user_and_fund(user.id, transaction_in.fund_id)
    fund_transactions.sort(key=lambda t: t.timestamp)

    # Determinar si el usuario tiene una suscripción activa
    active_subscription = None
    for t in fund_transactions:
        if t.transaction_type == TransactionType.SUBSCRIBE:
            active_subscription = t
        elif t.transaction_type == TransactionType.CANCEL:
            active_subscription = None

    # Manejar la logica para la transacción de suscripción o cancelación
    if transaction_in.transaction_type == TransactionType.SUBSCRIBE:
        # Verificar que el usuario no tenga una suscripción activa en el fondo en cuestión
        if active_subscription:
            raise HTTPException(status_code=400, detail=f"User is already subscribed to fund '{fund.name}'")
        # Verificar que el monto sea válido y que el usuario tenga saldo suficiente
        if transaction_in.amount is None:
            raise HTTPException(status_code=400, detail="Amount is required for subscription.")
        #Verificar que el monto sea mayor al minimo
        if transaction_in.amount < fund.min_amount:
            raise HTTPException(status_code=400, detail=f"Amount must be at least the minimum of {fund.min_amount}")
        #Verificar que el usuario tenga saldo suficiente
        if user.balance < transaction_in.amount:
            raise HTTPException(status_code=400, detail=f"No tiene saldo disponible para vincularse al fondo {fund.name}")

        new_balance = user.balance - transaction_in.amount

        # Actualizar el balance del usuario
        update_user_balance(user.id, new_balance)

        transaction_data = transaction_in.dict()
        transaction_data.update({
            "user_id": user.id,
            "timestamp": datetime.now(timezone.utc)
        })

        # Crear la transacción
        new_transaction = create_transaction(transaction_data)
        send_message(user=user,
                     subject="Subscription Successful",
                     body=f"You have successfully subscribed to the fund '{fund.name}' with an amount of {transaction_in.amount}.")
        return new_transaction

    elif transaction_in.transaction_type == TransactionType.CANCEL:
        # Verificar que el usuario tenga una suscripción activa en el fondo en cuestión
        if not active_subscription:
            raise HTTPException(status_code=400, detail=f"User is not subscribed to fund '{fund.name}'")

        # Revertir el balance del usuario
        refund_amount = active_subscription.amount
        new_balance = user.balance + refund_amount
        update_user_balance(user.id, new_balance)

        # Crear la transacción de cancelación
        transaction_data = {
            "user_id": user.id,
            "fund_id": active_subscription.fund_id,
            "amount": refund_amount,
            "transaction_type": TransactionType.CANCEL.value,
            "timestamp": datetime.now(timezone.utc)
        }

        # Crear la transacción
        new_transaction = create_transaction(transaction_data)
        # TODO: Send notification based on user.notif_options
        return new_transaction


def send_message(user: UserOut, subject: str, body: str):
    print(user.notif_options, "Notification Option")
    if user.notif_options == NotificationOptions.email:
        message = Message(
            subject=subject,
            body=body,
            recipient=user.email
        )
        email_notifier.send(message=message, email=user.email)
    elif user.notif_options == NotificationOptions.sms:
        message = Message(
            subject=subject,
            body=body,
            recipient=user.phone
        )
        sms_notifier.send(message=message, phone=user.phone)