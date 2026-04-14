from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

class TransactionCreate(BaseModel):
    transaction_id: str = Field(..., description="Unique transaction identifier")
    user_id: str = Field(..., description="User ID driving the transaction")
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    currency: str = Field(..., description="Currency code, e.g. USD, EUR, TWD")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)

    @field_validator('currency')
    @classmethod
    def currency_must_be_supported(cls, v: str) -> str:
        supported = ['USD', 'EUR', 'GBP', 'JPY', 'TWD']
        if v.upper() not in supported:
            raise ValueError(f"Currency {v} is not supported. Supported currencies: {supported}")
        return v.upper()

class TransactionResponse(BaseModel):
    transaction_id: str
    status: str
    message: str
