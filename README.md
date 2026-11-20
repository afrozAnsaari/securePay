# SecurePay

SecurePay is a UPI-style payment portal. It screens every peer-to-peer transfer
with a fraud-detection model (XGBoost trained on the
[PaySim](https://www.kaggle.com/datasets/ealaxi/paysim1) dataset) before any
money moves.

The project has three parts:

- **Simulated bank.** Customers, bank accounts and debit/credit cards (with
  Luhn-valid card numbers and real BIN ranges).
- **UPI layer.** Users, UPI profiles, linking bank accounts, UPI PINs, balance
  checks, payments and transaction history.
- **React frontend.** Lets a user register, log in, link accounts, send money
  and view transactions.

---

## Features

**Payments**
- P2P transfers addressed by mobile number or UPI ID.
- Money is stored as `Numeric(12, 2)` and handled as `Decimal` from end to end,
  never as `float`.
- Double-entry bookkeeping: every payment writes a `DEBIT` and a `CREDIT`
  ledger entry.
- The two account rows are locked with `SELECT … FOR UPDATE`, always in
  ascending account-id order, so concurrent transfers in opposite directions
  cannot deadlock.
- One database transaction covers the balance changes, the payment, the ledger
  entries, the idempotency record and the audit log. Either all of it commits
  or none of it does.
- Each payment gets a random 12-digit transaction reference. If a reference
  collides, a new one is tried inside a savepoint.

**Idempotency**
- `POST /upi/pay` requires an `Idempotency-Key` header.
- Redis is a fast cache of completed responses (24 h TTL). PostgreSQL is the
  source of truth, enforced by a `UNIQUE (user_id, idempotency_key)` constraint.
- A SHA-256 fingerprint of the request body detects a key being reused for a
  different payment, which returns `409`.

**Fraud detection**
- Features are built from the sender's and receiver's balances before and after
  the transfer, plus the transaction type.
- The model returns a risk score that maps to a decision (both thresholds
  are set in `config.json`):
  - `≤ 0.40`: `APPROVED`
  - between the two thresholds: `REVIEW`. The payment goes through, but it is
    stored with `fraud_decision = REVIEW` and a `PAYMENT_FLAGGED_FOR_REVIEW`
    audit event is written. The sender isn't told.
  - `≥ 0.90`: `DECLINED`. No money moves, and the attempt goes to the
    security audit log.
- The model runs before any row locks are taken, so no locks are held during
  inference.

**Security**
- Access tokens are JWTs (HS256, 1 h). Refresh tokens are opaque, last 7 days,
  and are stored only as SHA-256 hashes so they can be revoked.
- Passwords and UPI PINs are hashed with bcrypt.
- Sensitive card data is encrypted with Fernet.
- Rate limiting uses a sliding window in Redis, implemented as an atomic Lua
  script. Limits are per IP for login and registration, and per user for
  payments, balance checks, refresh and account linking.
- UPI PIN lockout: 5 wrong PINs lock the UPI profile for 15 minutes.
- Login returns the same error (after the same bcrypt work) for an unknown
  number and for a wrong password, so it doesn't reveal who is registered.
- The bank simulator routes are owner-only (see
  [Bank simulator (admin)](#bank-simulator-admin)).
- Every secret comes from `.env`. The app refuses to start if one is missing.
- Audit logs cover logins, logouts, account linking and payments. A separate
  security audit log records failed PINs and blocked frauds.

---

## Tech stack

| Layer    | Tech                                                        |
|----------|-------------------------------------------------------------|
| API      | Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.0           |
| Data     | PostgreSQL, Redis                                           |
| ML       | XGBoost, scikit-learn, pandas, joblib (notebooks in Jupyter)|
| Frontend | React 19, Vite                                              |
| Tooling  | `uv` or pip (Python), npm                                   |

---

## Project structure

```
securePay/
├── backend/
│   ├── notebooks/            # EDA + model training (PaySim, credit-card)
│   ├── reports/figures/      # Plots produced by the notebooks
│   ├── pyproject.toml        # Dependencies (uv) + uv.lock
│   ├── requirements*.txt     # Same pins, for pip
│   └── src/
│       ├── api/
│       │   ├── app.py        # FastAPI app, CORS, router registration
│       │   └── routes/
│       │       ├── bank/     # customers, accounts, card issuance
│       │       └── upi/      # auth, profiles, linking, payments, history
│       ├── auth/             # JWT, current-user dependency, PIN checks
│       ├── config/           # rate limits, card BINs
│       ├── core/             # logging, audit event names
│       ├── databases/
│       │   ├── postgres/     # engine/session, ORM models, CRUD
│       │   └── redis/        # Redis client
│       ├── exceptions/
│       ├── models/paysim/    # trained model (.joblib) + threshold config
│       ├── schemas/          # Pydantic request/response models
│       ├── security/         # hashing, encryption, Luhn, card networks
│       ├── services/
│       │   ├── payment/      # payment processing, receiver resolution, refs
│       │   ├── fraud/        # feature building + prediction
│       │   ├── redis/        # idempotency + rate limiting
│       │   ├── audit/        # audit log writer
│       │   └── auth/         # refresh-token service
│       └── utils/            # enums, generators, formatters
├── frontend/
│   └── src/
│       ├── api/              # fetch client with token refresh
│       ├── components/       # layout, modals, common UI
│       ├── context/          # AuthContext
│       ├── pages/            # Login, Register, Dashboard, Accounts,
│       │                     # SendMoney, Transactions, TransactionDetails
│       └── utils/            # validators, formatters, idempotency keys
└── secure_pay_backup.dump    # PostgreSQL schema/data dump (pg_dump -Fc)
```

---

## Getting started

### Prerequisites

- Python 3.11.9+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+ and npm
- PostgreSQL 16+
- Redis 6+

### 1. Database

The project has no migrations yet. To create the schema, restore the dump that
ships with the repo:

```bash
createdb secure_pay
pg_restore --no-owner -d secure_pay secure_pay_backup.dump
```

### 2. Backend

You can use **uv** or plain **pip**. Both install the same pinned versions.

**Option A: uv**

```bash
cd backend
uv sync                 # app + dev tools (jupyterlab, ipykernel, black)
# uv sync --no-dev      # app only
```

**Option B: pip**

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # app only
pip install -r requirements-dev.txt  # optional: notebooks / formatting
```

Then configure the environment:

```bash
cp .env.example .env
```

Fill in `.env`. Each required value has a generator command next to it in
`.env.example`.

| Variable              | Required | Purpose                                              |
|-----------------------|----------|------------------------------------------------------|
| `DATABASE_URL`        | yes      | `postgresql+psycopg2://user:pass@localhost:5432/secure_pay` |
| `ENCRYPTION_KEY`      | yes      | Fernet key for card numbers / KYC data               |
| `JWT_SECRET_KEY`      | yes      | Signs access tokens (≥ 32 chars)                     |
| `ADMIN_API_KEY`       | yes*     | Owner key for the bank simulator (≥ 32 chars)        |
| `REDIS_URL`           | no       | Default `redis://localhost:6379/0`                   |
| `CORS_ORIGINS`        | no       | Comma-separated; default is the Vite dev server      |
| `ACCESS_TOKEN_EXPIRE_MINUTES` / `REFRESH_TOKEN_EXPIRE_DAYS` | no | Default 60 / 7 |
| `ENABLE_ADMIN_ROUTES` | no       | Default `true`. Set `false` on a public deployment   |

\* Only required while `ENABLE_ADMIN_ROUTES` is `true`.

The trained model `src/models/paysim/xgboost_paysim_model.joblib` is ignored by
git (`*.joblib`). If you don't have it, regenerate it by running
`notebooks/paysim/02_xgboost_model.ipynb`.

Start Redis, then run the API **from the `backend/` directory**, because the
imports are rooted at `src.`:

```bash
uv run uvicorn src.api.app:app --reload     # uv
uvicorn src.api.app:app --reload            # pip (with the venv activated)
```

**Changing dependencies.** `pyproject.toml` and `uv.lock` are the source of
truth. After `uv add <pkg>` (or `uv add --group dev <pkg>`), regenerate the
pip files so they stay in sync:

```bash
./scripts/export_requirements.sh
```

The API runs at http://127.0.0.1:8000, with interactive docs at
http://127.0.0.1:8000/docs.

### 3. Frontend

```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

The app runs at http://localhost:5173. The backend's CORS settings allow this
origin.

---

## Bank simulator (admin)

The "bank side" of the project is separate from the app. App users can't
reach it, and the frontend never calls it. These routes only work when the
request carries your `ADMIN_API_KEY` in the `X-Admin-Key` header:

| Route                   | What it does                                    |
|-------------------------|-------------------------------------------------|
| `POST /bank/customers`  | Create a KYC-verified bank customer             |
| `POST /bank/accounts`   | Open an account with an opening balance         |
| `POST /cards/issuance`  | Issue a debit card. Returns the card number once |
| `POST /admin/predict`   | Run the fraud model on raw PaySim-style input   |

Without the key they return `401`, and with a wrong key they return `403`.
The easiest way to use them is http://127.0.0.1:8000/docs: click
**Authorize**, then paste the key. Or use curl:

```bash
curl -X POST http://127.0.0.1:8000/bank/customers \
  -H "X-Admin-Key: $ADMIN_API_KEY" -H "Content-Type: application/json" \
  -d '{"full_name":"Asha Test","dob":"1995-01-01","mobile_no":"9000000001",
       "email":"asha@example.com","aadhar_no":"123412341234",
       "pan_no":"ABCDE1234F","address":"Pune"}'
```

Set `ENABLE_ADMIN_ROUTES=false` to remove these routes from the API entirely.

## Typical flow

1. **Bank setup (admin).** `POST /bank/customers`, then `POST /bank/accounts`,
   then `POST /cards/issuance`. The customer's mobile number must match the
   number the user registers with in the app.
2. **Register / log in.** `POST /users/register`, then `POST /auth/login`,
   which returns an access token and a refresh token.
3. **Create a UPI profile.** `POST /upi/create-profile`.
4. **Discover and link accounts.** `POST /discover-accounts` returns the
   accounts registered to your own mobile number. Then call
   `POST /upi/link-bank` with the card details.
5. **Check balance.** `POST /accounts/get-balance` (requires the UPI PIN).
6. **Pay.** `POST /upi/pay` with the `Idempotency-Key` header.
7. **History.** The transaction endpoints under `/upi`.

Example payment:

```bash
curl -X POST http://127.0.0.1:8000/upi/pay \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Idempotency-Key: $(uuidgen)" \
  -H "Content-Type: application/json" \
  -d '{
        "receiver": "someone@securepay",
        "sender_upi_profile_id": 1,
        "sender_account_id": 1,
        "amount": "250.00",
        "upi_pin": "1234"
      }'
```

| Status | Meaning                                                      |
|--------|--------------------------------------------------------------|
| 200    | Success (or a replayed response for the same idempotency key)|
| 400    | Bad input / insufficient balance                             |
| 403    | Wrong UPI PIN (shows attempts left), or declined as fraud    |
| 409    | Idempotency key reused for a different payment, or in flight |
| 429    | Rate-limited, or UPI PIN locked (see `Retry-After`)          |
| 503    | Redis unavailable (rate limiter fails closed)                |

---

## Payment pipeline

```
POST /upi/pay
  ├─ validate Idempotency-Key
  ├─ rate limit (Redis, per user)
  ├─ Redis idempotency cache ──hit──► return cached response
  ├─ Postgres idempotency row ──exists──► return saved payment / 409
  ├─ INSERT idempotency row (UNIQUE constraint decides who wins a race)
  └─ process_payment_transaction()
       ├─ sender UPI profile + PIN check
       ├─ resolve receiver → primary linked account
       ├─ pre-check balance
       ├─ fraud model → APPROVED / REVIEW / DECLINED
       ├─ lock both accounts (ordered by id, fresh read via populate_existing)
       ├─ re-check balance, move funds
       ├─ insert Payment (retry on reference collision)
       └─ insert DEBIT + CREDIT ledger entries
  ├─ audit log
  ├─ COMMIT (single transaction)
  └─ cache the response in Redis
```

---

## Fraud model

The model was trained in `backend/notebooks/paysim/`. It uses these features
(listed in `src/utils/feature_columns.py`):

`step, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest, newbalanceDest,
origBalanceDiff, type_CASH_OUT, type_DEBIT, type_PAYMENT, type_TRANSFER`

| App transaction type | PaySim type |
|----------------------|-------------|
| `P2P`                | `TRANSFER`  |
| `P2M`                | `PAYMENT`   |
| `BANK_DEBIT`         | `DEBIT`     |
| `ATM_WITHDRAWAL`     | `CASH_OUT`  |

Both thresholds (`threshold` for declining, `review_threshold` for flagging)
are set in `backend/src/models/paysim/config.json`.

`step` is "hours since the start of a 30-day simulation" in PaySim. The app
uses the hour of the current month (1–743) to match it.

---

## License

No license has been chosen yet.
