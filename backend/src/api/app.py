from fastapi import FastAPI


from src.databases.database import engine
from src.databases.models import Base

from src.schemas.transaction import Transaction

from src.api.routes import (
    users,
)


from src.api.routes import accounts

from src.api.routes.upi.audit import router as test_audit_log

from src.api.routes.bank.customers import router as customer_router
from src.api.routes.bank.accounts import router as bank_account_router
from src.api.routes.bank.card_issuance import router as card_issuance_router

from src.api.routes.upi.login import router as login_router
from src.api.routes.upi.logout import router as logout_router
from src.api.routes.upi.accounts import router as get_all_user_linked_accounts
from src.api.routes.upi.profiles import router as UPI_Route
from src.api.routes.upi.fetch_accounts import router as discover_accounts
from src.api.routes.upi.link_bank_account import router as link_bank_router
from src.api.routes.upi.check_upi_profile import router as check_upi_account
from src.api.routes.upi.payments import router as make_payments_router
from src.api.routes.upi.transactions import router as transaction_history_router
from src.api.routes.upi.refresh_token import router as refresh_token_auth


from src.services.fraud.predictor import predict_fraud

import logging

from fastapi import FastAPI

from src.core.logging_config import setup_logging

setup_logging()

logger = logging.getLogger(__name__)

logger.info("SecurePay logging system initialized")


app = FastAPI()


app.include_router(test_audit_log)
app.include_router(refresh_token_auth)
app.include_router(login_router)
app.include_router(logout_router)
app.include_router(get_all_user_linked_accounts)
app.include_router(check_upi_account)
app.include_router(link_bank_router)
app.include_router(discover_accounts)
app.include_router(UPI_Route)
app.include_router(card_issuance_router)
app.include_router(bank_account_router)
app.include_router(customer_router)
app.include_router(make_payments_router)
app.include_router(transaction_history_router)
app.include_router(users.router)
app.include_router(accounts.router)


@app.get("/")
def home():

    return {"message": "Fraud Detection API Running"}


@app.post("/predict")
def predict(transaction: Transaction):

    result = predict_fraud(transaction.model_dump())

    return result
