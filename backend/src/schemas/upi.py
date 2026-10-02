from pydantic import BaseModel


class UPIProfileRespnse(BaseModel):

    exists: bool

    id: int | None = None

    upi_id: str | None = None

    upi_pin_exists: bool
