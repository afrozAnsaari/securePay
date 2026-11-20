"""
Fill an empty SecurePay database with FAKE demo data:
bank customers, accounts, debit cards, app users, UPI IDs,
linked accounts and a few real payments (run through the actual
payment pipeline, so balances, ledger entries and fraud scores are genuine).

Every name, number and email here is made up. Never seed real people.

Usage (from backend/, with Redis running, because the UPI PIN check uses it):
    DATABASE_URL="<neon connection string>" python scripts/seed_demo.py

    # Wipe ALL data in that database and seed again (asks for confirmation):
    DATABASE_URL="<neon connection string>" python scripts/seed_demo.py --reset
"""

import argparse
from datetime import date
from decimal import Decimal

import _bootstrap  # noqa: F401  (sets up imports)

from src.databases.postgres.crud import (
    create_account,
    create_card,
    create_customer,
    create_upi_profile,
    create_user,
    link_bank_acc,
)
from src.databases.postgres.database import SessionLocal, engine
from src.databases.postgres.models import Base, User
from src.schemas.account import AccountCreate
from src.schemas.card import CardCreate
from src.schemas.customer import CustomerCreate
from src.schemas.link_bank_request import LinkBankRequest
from src.schemas.payment import PaymentCreate
from src.schemas.upi_profile import UPIProfileCreate
from src.schemas.user import UserCreate
from src.services.payment.payment_service import process_payment_transaction

PASSWORD = "123456"  # app login password (the login form accepts 4-6 digits)
UPI_PIN = "1234"
CARD_PIN = "1111"

# fmt: off
PEOPLE = [
    {
        "name": "Priya Sharma", "mobile": "9000000001", "upi": "priya",
        "dob": date(1998, 4, 12), "aadhar": "100000000001", "pan": "AAAPS1001A",
        "accounts": [("SBI", "SAVINGS", "52000.00", True), ("HDFC", "SAVINGS", "18500.00", False)],
    },
    {
        "name": "Rahul Verma", "mobile": "9000000002", "upi": "rahul",
        "dob": date(1995, 9, 3), "aadhar": "100000000002", "pan": "AAAPV1002B",
        "accounts": [("ICICI", "SAVINGS", "26000.00", True)],
    },
    {
        "name": "Ananya Iyer", "mobile": "9000000003", "upi": "ananya",
        "dob": date(2000, 1, 21), "aadhar": "100000000003", "pan": "AAAPI1003C",
        "accounts": [("HDFC", "CURRENT", "84000.00", True)],
    },
]

# (sender upi, receiver upi, amount): small enough that the model approves them
PAYMENTS = [
    ("priya", "rahul", "750.00"),
    ("rahul", "ananya", "1200.00"),
    ("ananya", "priya", "2500.00"),
    ("priya", "ananya", "320.00"),
]
# fmt: on


def reset_database() -> None:
    target = _bootstrap.describe_target()
    print(f"\n!!! --reset will DELETE ALL DATA in {target} !!!")
    answer = input("Type the database host to confirm: ").strip()
    if answer != target.split(":")[0]:
        raise SystemExit("Aborted. Nothing was changed.")
    Base.metadata.drop_all(engine)
    print("All tables dropped.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="drop all tables first (asks to confirm)")
    args = parser.parse_args()

    print(f"Target database: {_bootstrap.describe_target()}")

    if args.reset:
        reset_database()

    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            raise SystemExit(
                "This database already has users, so nothing was seeded.\n"
                "Run with --reset to wipe it and seed fresh demo data."
            )

        users, profiles, primary_accounts, unlinked_cards = {}, {}, {}, []

        for p in PEOPLE:
            email = p["upi"] + "@example.com"

            customer = create_customer(db, CustomerCreate(
                full_name=p["name"], dob=p["dob"], mobile_no=p["mobile"], email=email,
                aadhar_no=p["aadhar"], pan_no=p["pan"], address="Demo Street, Pune",
            ))

            create_user(db, UserCreate(name=p["name"], mobile_no=p["mobile"], email=email, password=PASSWORD))
            user = db.query(User).filter(User.mobile_no == p["mobile"]).one()
            users[p["upi"]] = user

            profile = create_upi_profile(db, UPIProfileCreate(upi_id=p["upi"], upi_pin=UPI_PIN), user)
            profiles[p["upi"]] = profile["profile_id"]

            for bank, acc_type, balance, link_now in p["accounts"]:
                account = create_account(db, AccountCreate(
                    customer_id=customer.id, bank_name=bank, account_type=acc_type,
                    initial_balance=Decimal(balance), mobile_no=p["mobile"],
                ))
                card = create_card(CardCreate(account_id=account.id, network="RUPAY", card_pin=CARD_PIN), db)

                if link_now:
                    link_bank_acc(LinkBankRequest(
                        bank_name=bank, card_number=card["card_number"],
                        expiry_month=card["expiry_month"], expiry_year=card["expiry_year"], card_pin=CARD_PIN,
                    ), db, user)
                    db.commit()
                    primary_accounts[p["upi"]] = account.id
                else:
                    unlinked_cards.append((p, bank, card))

        print("\nRunning demo payments through the real payment pipeline...")
        for sender, receiver, amount in PAYMENTS:
            payment = process_payment_transaction(
                db=db,
                payment_data=PaymentCreate(
                    receiver=f"{receiver}@securepay",
                    sender_upi_profile_id=profiles[sender],
                    sender_account_id=primary_accounts[sender],
                    amount=Decimal(amount),
                    upi_pin=UPI_PIN,
                ),
                current_user=users[sender],
            )
            db.commit()
            print(f"  {sender} -> {receiver}  Rs {amount}  "
                  f"(txn {payment.transaction_id}, risk {payment.risk_score:.4f}, {payment.fraud_decision})")

    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

    print("\n================ DEMO LOGINS (all data is fake) ================")
    print(f"Password for every user: {PASSWORD}     UPI PIN: {UPI_PIN}")
    for p in PEOPLE:
        print(f"  {p['name']:<14} mobile {p['mobile']}   UPI ID {p['upi']}@securepay")
    print("\nNot linked yet, so you can show 'Link bank account' live:")
    for p, bank, card in unlinked_cards:
        print(f"  {p['name']} / {bank}: card {card['card_number']}  "
              f"exp {card['expiry_month']:02d}/{card['expiry_year']}  card PIN {CARD_PIN}")
    print("================================================================")


if __name__ == "__main__":
    main()
