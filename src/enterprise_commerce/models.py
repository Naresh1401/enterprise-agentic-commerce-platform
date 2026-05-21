from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Product(BaseModel):
    sku: str
    title: str
    price: Decimal
    inventory: int
    currency: str = "USD"


class OrderItem(BaseModel):
    sku: str
    quantity: int = Field(gt=0, le=50)


class QuoteRequest(BaseModel):
    customer_id: str
    items: list[OrderItem] = Field(min_length=1, max_length=20)
    destination_zip: str = Field(min_length=5, max_length=10)

    @field_validator("customer_id")
    @classmethod
    def scoped_customer_id(cls, value: str) -> str:
        if not value.startswith("cust_"):
            raise ValueError("customer_id must start with cust_")
        return value


class QuoteResponse(BaseModel):
    quote_id: str
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    total: Decimal
    available: bool
    warnings: list[str] = []


class CheckoutMandate(BaseModel):
    mandate_id: str
    shopper_id: str
    checkout_hash: str = Field(min_length=16)
    max_total: Decimal
    signed_by_trusted_surface: bool


class CheckoutRequest(QuoteRequest):
    payment_token: str = Field(min_length=8)
    mandate: CheckoutMandate


class CheckoutResponse(BaseModel):
    order_id: str
    status: Literal["accepted"]
    authorization_id: str
    fulfillment_id: str
    quote: QuoteResponse


class NormalizedOffer(BaseModel):
    partner_id: str
    sku: str
    title: str
    price: Decimal
    availability: str
    source_ref: str
    attributes: dict[str, Any] = Field(default_factory=dict)


class ToolInvocation(BaseModel):
    name: Literal["catalog.search", "commerce.quote", "commerce.checkout"]
    arguments: dict[str, Any]
    approved_by_human: bool = False


class AgenticEvalResult(BaseModel):
    accepted: bool
    reasons: list[str] = []

