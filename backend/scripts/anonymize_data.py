"""
Replace every real identity in a SecurePay database with fake ones, while
keeping all accounts, balances, cards, links, payments and ledger entries.

What changes:
  users          name, mobile, email -> fake; password -> DEMO_PASSWORD
  customers      name, DOB, mobile, email, address, Aadhaar, PAN -> fake
  accounts       mobile -> the owner's new fake mobile (kept consistent)
  upi_profiles   UPI ID -> fake handle; UPI PIN -> DEMO_UPI_PIN
  cards          card PIN -> DEMO_CARD_PIN (card numbers are synthetic already)
  audit_logs     IP address and browser info removed; old mobiles / UPI IDs
                 inside the metadata replaced with the new fake ones
  refresh_tokens deleted (old login sessions)

Mobile numbers are mapped consistently across users, customers and accounts,
so "link bank account" (which matches customer mobile to user mobile) still
works afterwards.

Usage (from backend/):
    DATABASE_URL="<connection string>" python scripts/anonymize_data.py
It shows the target database and asks you to type its host before changing
anything. All changes happen in one transaction: either everything is
anonymized or nothing is.
"""

import _bootstrap  # noqa: F401  (sets up imports)

import hashlib
from datetime import date

from src.databases.postgres.database import SessionLocal
from src.databases.postgres.models import (
    Account,
    AuditLog,
    Card,
    Customer,
    RefreshToken,
    UPIProfile,
    User,
)
from src.security.encryption import encrypt_data
from src.security.password import hash_password

DEMO_PASSWORD = "123456"
DEMO_UPI_PIN = "1234"
DEMO_CARD_PIN = "1111"

FAKE_NAMES = [
    "Priya Sharma", "Rahul Verma", "Ananya Iyer", "Arjun Mehta", "Sneha Kulkarni",
    "Karan Malhotra", "Meera Nair", "Rohan Desai", "Ishita Rao", "Vikram Joshi",
    "Neha Kapoor", "Aditya Singh", "Pooja Reddy", "Siddharth Jain", "Kavya Menon",
    "Aman Gupta", "Riya Banerjee", "Nikhil Patil", "Tanvi Shah", "Dev Chauhan",
]


def fake_identity(n: int) -> dict:
    """n starts at 1. Everything is derived from n, so it's stable and unique."""
    name = FAKE_NAMES[(n - 1) % len(FAKE_NAMES)]
    if n > len(FAKE_NAMES):
        name += f" {n}"
    first = name.split()[0].lower()
    handle = first if n <= len(FAKE_NAMES) else f"{first}{n}"
    return {
        "name": name,
        "handle": handle,
        "mobile": f"90000{n:05d}",
        "email": f"{handle}@example.com",
        "dob": date(1990 + n % 12, (n % 12) + 1, (n % 27) + 1),
        "aadhar": f"1000{n:08d}",
        "pan": f"AAAP{chr(65 + n % 26)}{n:04d}{chr(65 + (n * 7) % 26)}",
        "address": f"{n} Demo Street, Pune",
    }


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def replace_in_json(value, mapping: dict):
    if isinstance(value, str):
        return mapping.get(value.strip().lower(), value)
    if isinstance(value, dict):
        return {k: replace_in_json(v, mapping) for k, v in value.items()}
    if isinstance(value, list):
        return [replace_in_json(v, mapping) for v in value]
    return value


def main() -> None:
    target = _bootstrap.describe_target()
    host = target.split(":")[0]

    db = SessionLocal()
    try:
        users = db.query(User).order_by(User.id).all()
        customers = db.query(Customer).order_by(Customer.id).all()

        print(f"Target database: {target}")
        print(f"Found {len(users)} users and {len(customers)} bank customers.")
        if host in {"localhost", "127.0.0.1"}:
            print("NOTE: this is your LOCAL database. It will be anonymized too.")

        answer = input(f"Type the database host ({host}) to anonymize it: ").strip()
        if answer != host:
            raise SystemExit("Aborted. Nothing was changed.")

        # ---- one fake identity per real person, keyed by mobile number --------
        identity_by_mobile: dict[str, dict] = {}

        def identity_for(mobile: str) -> dict:
            if mobile not in identity_by_mobile:
                identity_by_mobile[mobile] = fake_identity(len(identity_by_mobile) + 1)
            return identity_by_mobile[mobile]

        for user in users:
            identity_for(user.mobile_no)
        for customer in customers:
            identity_for(customer.mobile_no)

        # Work out each user's new UPI handle now, while users still have
        # their original mobile numbers.
        handle_by_user = {u.id: identity_for(u.mobile_no)["handle"] for u in users}

        # old value (lower-case) -> new value, for scrubbing audit metadata
        text_mapping: dict[str, str] = {}

        # ---- users -------------------------------------------------------------
        demo_password_hash = hash_password(DEMO_PASSWORD)
        for user in users:
            fake = identity_for(user.mobile_no)
            text_mapping[user.mobile_no] = fake["mobile"]
            text_mapping[user.email.lower()] = fake["email"]
            user.name = fake["name"]
            user.mobile_no = fake["mobile"]
            user.email = fake["email"]
            user.password_hash = demo_password_hash
            if getattr(user, "payment_pin_hash", None) is not None:
                user.payment_pin_hash = hash_password(DEMO_UPI_PIN)

        # ---- customers ---------------------------------------------------------
        for customer in customers:
            fake = identity_for(customer.mobile_no)
            customer.full_name = fake["name"]
            customer.dob = fake["dob"]
            customer.mobile_no = fake["mobile"]
            customer.email = fake["email"]
            customer.address = fake["address"]
            customer.aadhar_hash = sha256(fake["aadhar"])
            customer.aadhar_encrypted = encrypt_data(fake["aadhar"])
            customer.pan_hash = sha256(fake["pan"])
            customer.pan_encrypted = encrypt_data(fake["pan"])

        # ---- accounts: keep mobiles consistent with their owners ---------------
        for account in db.query(Account).all():
            account.mobile_no = identity_for(account.mobile_no)["mobile"]

        # ---- UPI profiles ------------------------------------------------------
        demo_upi_pin_hash = hash_password(DEMO_UPI_PIN)
        used_handles: set[str] = set()
        profiles = db.query(UPIProfile).order_by(UPIProfile.id).all()

        # Give every profile a temporary unique ID first, so renaming can't
        # collide with an old ID that hasn't been renamed yet.
        for profile in profiles:
            text_mapping[profile.upi_id.lower()] = None  # filled in below
            profile.upi_id = f"tmp{profile.id}@securepay"
        db.flush()

        old_ids = [k for k, v in text_mapping.items() if v is None]
        for profile, old_id in zip(profiles, old_ids):
            base = handle_by_user.get(profile.user_id, "demo")
            handle, n = base, 2
            while handle in used_handles:
                handle, n = f"{base}{n}", n + 1
            used_handles.add(handle)
            profile.upi_id = f"{handle}@securepay"
            profile.upi_pin_hash = demo_upi_pin_hash
            text_mapping[old_id] = profile.upi_id
            text_mapping[old_id.removesuffix("@securepay")] = profile.upi_id

        # ---- cards: reset PINs -------------------------------------------------
        demo_card_pin_hash = hash_password(DEMO_CARD_PIN)
        for card in db.query(Card).all():
            card.card_pin_hash = demo_card_pin_hash

        # ---- audit logs --------------------------------------------------------
        for log in db.query(AuditLog).all():
            log.ip_address = None
            log.user_agent = None
            if log.metadata_json:
                log.metadata_json = replace_in_json(log.metadata_json, text_mapping)

        # ---- old login sessions ------------------------------------------------
        deleted_tokens = db.query(RefreshToken).delete()

        db.commit()

    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()

    print(f"\nDone. Removed {deleted_tokens} old login session(s).")
    print("\n============ DEMO LOGINS (all identities are fake) ============")
    print(f"Password for every user: {DEMO_PASSWORD}   UPI PIN: {DEMO_UPI_PIN}   "
          f"Card PIN: {DEMO_CARD_PIN}")

    db = SessionLocal()
    try:
        for user in db.query(User).order_by(User.id).all():
            upi_ids = [
                p.upi_id
                for p in db.query(UPIProfile).filter(UPIProfile.user_id == user.id)
            ]
            print(f"  {user.name:<18} mobile {user.mobile_no}   "
                  f"UPI {', '.join(upi_ids) or '(none yet)'}")
    finally:
        db.close()
    print("================================================================")


if __name__ == "__main__":
    main()
