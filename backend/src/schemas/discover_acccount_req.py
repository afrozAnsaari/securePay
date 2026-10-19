from pydantic import BaseModel


class DiscoverAccountsRequest(BaseModel):
    user_id: int
    mobile_no: str
