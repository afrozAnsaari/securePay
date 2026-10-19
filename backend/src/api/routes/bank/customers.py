from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from src.databases.postgres.database import get_db

from src.schemas.customer import CustomerCreate

from src.databases.postgres.crud import create_customer

router = APIRouter(
    prefix="/bank",
    tags=["Bank Customers"],
)


@router.post("/customers")
def register_customer(
    customer: CustomerCreate,
    db: Session = Depends(get_db),
):

    created_customer = create_customer(
        db,
        customer,
    )

    return {
        "customer_id": created_customer.id,
        "full_name": created_customer.full_name,
        "kyc_verified": created_customer.kyc_verified,
    }
