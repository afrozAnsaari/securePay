import logging
import re
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import settings
from src.core.logging_config import request_id_ctx, setup_logging
from src.exceptions.payments_exceptions import TransactionReferenceGenerationError

from src.api.routes import accounts, health, users

from src.api.routes.upi.login import router as login_router
from src.api.routes.upi.logout import router as logout_router
from src.api.routes.upi.refresh_token import router as refresh_token_router
from src.api.routes.upi.get_linked_accounts import router as linked_accounts_router
from src.api.routes.upi.create_upi_profiles import router as create_upi_profile_router
from src.api.routes.upi.check_upi_profile import router as check_upi_profile_router
from src.api.routes.upi.fetch_accounts import router as discover_accounts_router
from src.api.routes.upi.link_bank_account import router as link_bank_router
from src.api.routes.upi.payments import router as payments_router
from src.api.routes.upi.transactions import router as transactions_router

setup_logging()

logger = logging.getLogger(__name__)

logger.info("SecurePay logging system initialized")


app = FastAPI(title="SecurePay API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# A client may send its own X-Request-ID (e.g. from a proxy); otherwise we
# make one. Only short, safe values are accepted so nobody can inject text
# into the logs.
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    incoming = request.headers.get("X-Request-ID", "")
    request_id = incoming if _REQUEST_ID_PATTERN.match(incoming) else uuid.uuid4().hex

    token = request_id_ctx.set(request_id)
    started = time.perf_counter()
    try:
        response = await call_next(request)

        response.headers["X-Request-ID"] = request_id

        if not request.url.path.startswith("/health"):
            logger.info(
                "%s %s -> %s (%.1f ms)",
                request.method,
                request.url.path,
                response.status_code,
                (time.perf_counter() - started) * 1000,
            )

        return response
    except Exception:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        raise
    finally:
        request_id_ctx.reset(token)


@app.exception_handler(TransactionReferenceGenerationError)
async def transaction_reference_exception_handler(
    request, exc: TransactionReferenceGenerationError
):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Unable to complete this transaction. Please try again later."
        },
    )


# ---------------------------------------------------------------
# App (user-facing) routes: used by the React frontend.
# ---------------------------------------------------------------

app.include_router(health.router)
app.include_router(users.router)
app.include_router(login_router)
app.include_router(logout_router)
app.include_router(refresh_token_router)
app.include_router(create_upi_profile_router)
app.include_router(check_upi_profile_router)
app.include_router(discover_accounts_router)
app.include_router(link_bank_router)
app.include_router(linked_accounts_router)
app.include_router(accounts.router)
app.include_router(payments_router)
app.include_router(transactions_router)


# ---------------------------------------------------------------
# Bank-simulator / admin routes: owner only (X-Admin-Key header).
# Set ENABLE_ADMIN_ROUTES=false to remove them entirely.
# ---------------------------------------------------------------

if settings.ENABLE_ADMIN_ROUTES:
    from src.api.routes.admin import router as admin_router
    from src.api.routes.bank.accounts import router as bank_account_router
    from src.api.routes.bank.card_issuance import router as card_issuance_router
    from src.api.routes.bank.customers import router as customer_router

    app.include_router(customer_router)
    app.include_router(bank_account_router)
    app.include_router(card_issuance_router)
    app.include_router(admin_router)


@app.get("/")
def home():

    return {"message": "SecurePay API running"}
