from decimal import Decimal
from uuid import uuid4

from fastapi import HTTPException

from enterprise_commerce.auth import Principal
from enterprise_commerce.models import CheckoutMandate, CheckoutRequest, CheckoutResponse, Product, QuoteRequest, QuoteResponse


PRODUCTS = {
    "coffee": Product(sku="coffee", title="Cincinnati Coffee", price=Decimal("12.99"), inventory=30),
    "mug": Product(sku="mug", title="Agentic Commerce Mug", price=Decimal("9.50"), inventory=8),
    "hoodie": Product(sku="hoodie", title="API First Hoodie", price=Decimal("39.00"), inventory=0),
}


def validate_mandate(mandate: CheckoutMandate, total: Decimal) -> list[str]:
    reasons: list[str] = []
    if not mandate.signed_by_trusted_surface:
        reasons.append("mandate not signed by trusted surface")
    if total > mandate.max_total:
        reasons.append("checkout total exceeds mandate")
    return reasons


class CommerceOrchestrator:
    def list_products(self) -> list[Product]:
        return list(PRODUCTS.values())

    def quote(self, request: QuoteRequest, principal: Principal) -> QuoteResponse:
        if principal.tenant_id != "tenant_cincinnati":
            raise HTTPException(status_code=403, detail="Tenant denied")
        subtotal = Decimal("0.00")
        warnings: list[str] = []
        available = True
        for item in request.items:
            product = PRODUCTS.get(item.sku)
            if not product:
                available = False
                warnings.append(f"{item.sku} unknown")
                continue
            subtotal += product.price * item.quantity
            if product.inventory < item.quantity:
                available = False
                warnings.append(f"{item.sku} unavailable")
        tax = (subtotal * Decimal("0.075")).quantize(Decimal("0.01"))
        shipping = Decimal("0.00") if subtotal >= Decimal("50.00") else Decimal("4.99")
        return QuoteResponse(
            quote_id=f"quote_{uuid4().hex[:10]}",
            subtotal=subtotal,
            tax=tax,
            shipping=shipping,
            total=subtotal + tax + shipping,
            available=available,
            warnings=warnings,
        )

    def checkout(self, request: CheckoutRequest, principal: Principal) -> CheckoutResponse:
        quote = self.quote(request, principal)
        if not quote.available:
            raise HTTPException(status_code=409, detail={"message": "Quote unavailable", "warnings": quote.warnings})
        mandate_errors = validate_mandate(request.mandate, quote.total)
        if mandate_errors:
            raise HTTPException(status_code=403, detail={"message": "Mandate rejected", "reasons": mandate_errors})
        return CheckoutResponse(
            order_id=f"order_{uuid4().hex[:10]}",
            status="accepted",
            authorization_id=f"auth_{request.payment_token[-4:]}",
            fulfillment_id=f"fulfillment_{request.destination_zip[:5]}",
            quote=quote,
        )

