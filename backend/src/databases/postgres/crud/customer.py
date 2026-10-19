import hashlib
from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.databases.postgres.models.customer import Customer
from src.schemas.customer import CustomerCreate
from src.security.encryption import encrypt_data
from src.security.hash_utils import sha256_hash


def create_customer(db: Session, customer_data: CustomerCreate):
    aadhar_hash = hashlib.sha256(customer_data.aadhar_no.encode()).hexdigest()
    pan_hash = hashlib.sha256(customer_data.pan_no.encode()).hexdigest()

    aadhar_encrypted = encrypt_data(customer_data.aadhar_no)
    pan_encrypted = encrypt_data(customer_data.pan_no)

    customer = Customer(
        full_name=customer_data.full_name,
        dob=customer_data.dob,
        mobile_no=customer_data.mobile_no,
        email=customer_data.email,
        aadhar_hash=aadhar_hash,
        aadhar_encrypted=aadhar_encrypted,
        pan_hash=pan_hash,
        pan_encrypted=pan_encrypted,
        address=customer_data.address,
        kyc_verified=True,
    )

    existing_aadhar = (
        db.query(Customer)
        .filter(Customer.aadhar_hash == sha256_hash(customer_data.aadhar_no))
        .first()
    )

    if existing_aadhar:
        raise HTTPException(
            status_code=409,
            detail="Customer with this Aadhar Number already exists...",
        )

    existing_pan = (
        db.query(Customer)
        .filter(Customer.pan_hash == sha256_hash(customer_data.pan_no))
        .first()
    )

    if existing_pan:
        raise HTTPException(
            status_code=409,
            detail="Customer with this PAN already exists...",
        )

    existing_email = (
        db.query(Customer).filter(Customer.email == customer_data.email).first()
    )

    if existing_email:
        raise HTTPException(
            status_code=409,
            detail="Customer with this email already exists. Pleas try another email",
        )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer
