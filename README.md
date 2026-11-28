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
│   ├── Dockerfile            # API image (multi-stage, non-root)
│   ├── alembic.ini
│   ├── migrations/           # Alembic database migrations
│   ├── notebooks/            # EDA + model training (PaySim, credit-card)
│   ├── reports/figures/      # Plots produced by the notebooks
│   ├── scripts/              # init_db, seed_demo, anonymize_data, export_requirements
│   ├── pyproject.toml        # Dependencies (uv) + uv.lock
│   ├── requirements*.txt     # Same pins, for pip
│   ├── tests/                # pytest (needs Postgres + Redis)
│   └── src/
│       ├── api/
│       │   ├── app.py        # FastAPI app, CORS, request IDs, router registration
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
├── docker-compose.yml        # backend locally: db, redis, migrate, api
├── render.yaml               # Render Blueprint (backend + Redis)
```

---

## Getting started

### Quick start with Docker

The backend (Postgres, Redis, migrations, API) starts with one command.
You need only Docker:

```bash
cp backend/.env.example backend/.env    # fill in ENCRYPTION_KEY, JWT_SECRET_KEY, ADMIN_API_KEY
docker compose up --build
```

- API: http://localhost:8000 (docs at `/docs`)
- Frontend: run it as usual (see [3. Frontend](#3-frontend)) at http://localhost:5173

`DATABASE_URL` and `REDIS_URL` in `.env` are ignored here, because compose
points the API at its own containers. For demo data, run
`docker compose exec api python scripts/seed_demo.py`.
`docker compose down -v` stops everything and deletes the database.

What starts, in order:

| Service   | What it does                                                         |
|-----------|----------------------------------------------------------------------|
| `db`      | Postgres 16 (also on `localhost:5433` for tests and psql)            |
| `redis`   | Redis 7 (also on `localhost:6380`)                                   |
| `migrate` | Runs `scripts/init_db.py` (Alembic migrations), then exits           |
| `api`     | FastAPI in a non-root container; starts only after `migrate` succeeds |

To run it without Docker, follow the steps below.

### Prerequisites

- Python 3.11.9+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+ and npm
- PostgreSQL 16+
- Redis 6+

### 1. Database

Create an empty database, then create the tables and (optionally) fake demo
data from the `backend/` folder:

```bash
createdb secure_pay
python scripts/init_db.py      # applies the Alembic migrations (safe to re-run)
python scripts/seed_demo.py    # fake users, accounts, cards, UPI IDs and payments
```

Both scripts use `DATABASE_URL` from `backend/.env`, unless you pass a
different one on the command line (e.g. a hosted database):
`DATABASE_URL="<url>" python scripts/init_db.py`.

`seed_demo.py` needs Redis running, because it sends real payments through
the payment pipeline. It refuses to run on a database that already has
users. `--reset` wipes everything and re-seeds, after you type the database
host to confirm. It prints the demo logins (password `123456`, UPI PIN `1234`).

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

The trained model `src/models/paysim/xgboost_paysim_model.joblib` is committed
to the repo (2.3 MB), and the API loads it when it starts. To retrain it, run
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

**Health checks.** `GET /health/live` only says the process is running.
`GET /health/ready` also checks Postgres and Redis, and returns 503 when
either is down. Every response carries an `X-Request-ID` header, and the
same ID appears on every log line for that request.

**Database migrations (Alembic).** The schema lives in `migrations/versions/`.
After changing a model:

```bash
alembic revision --autogenerate -m "describe the change"   # creates a migration; read it before committing
python scripts/init_db.py                                  # applies it (same as: alembic upgrade head)
```

Databases created before migrations existed already have the tables, so
`init_db.py` marks them as being at the first migration instead of creating
the tables again.

**Tests.** The tests use a real Postgres and Redis, because what they check
(row locks, unique constraints, the Redis cache) only exists there. Start them
with `docker compose up -d db redis`, then from `backend/`:

```bash
uv run pytest          # or: pytest (with the dev requirements installed)
```

They use their own `securepay_test` database and Redis DB 15, and wipe both
between tests. Set `TEST_DATABASE_URL` / `TEST_REDIS_URL` to use other servers.
Covered: concurrent double-spend, opposite-direction transfers (deadlock),
idempotency replay from Redis and from Postgres, key reuse, fraud decision
thresholds, a declined payment moving no money, and the health checks.

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

## Deploying (free tier)

| Part     | Where                    | Notes |
|----------|--------------------------|-------|
| Database | [Neon](https://neon.tech) free | Never expires. Use the **direct** connection string (host without `-pooler`) |
| Backend  | Render free web service  | Defined in `render.yaml`. Sleeps after 15 min idle, takes about 1 min to wake |
| Redis    | Render free Key Value    | Defined in `render.yaml`. Only reachable from the backend |
| Frontend | Vercel (Hobby)           | `frontend/vercel.json` |

**1. Database (Neon).** Create a project in the same region as the backend
(`render.yaml` uses Singapore), then from `backend/`:

```bash
read -rs NEON_URL                                  # paste the string, press Enter
DATABASE_URL="$NEON_URL" python scripts/init_db.py
DATABASE_URL="$NEON_URL" python scripts/seed_demo.py   # fake demo data
```

**2. Backend + Redis (Render).** Go to **New → Blueprint**, pick this repo,
and Render reads `render.yaml`. It asks for:

| Variable         | Value |
|------------------|-------|
| `DATABASE_URL`   | The Neon connection string |
| `ENCRYPTION_KEY` | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `CORS_ORIGINS`   | `http://localhost:5173` for now; replace with the Vercel URL in step 4 |

`JWT_SECRET_KEY` is generated by Render. `ENABLE_ADMIN_ROUTES` is `false`,
so the bank simulator routes don't exist online.

**3. Frontend (Vercel).** Go to **Add New → Project**, import this repo, set
**Root Directory** to `frontend`, add the environment variable
`VITE_API_URL=https://<your-service>.onrender.com`, then deploy.

**4. Connect them.** In Render, under **securepay-api → Environment**, set
`CORS_ORIGINS` to the Vercel production URL (e.g.
`https://securepay-xyz.vercel.app`, no trailing slash) and save. Render
redeploys automatically.

Open the backend URL a minute before a demo to wake it up.

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
