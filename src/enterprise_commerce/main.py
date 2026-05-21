from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException, Request

from enterprise_commerce.agentic_quality import evaluate_tool_call
from enterprise_commerce.auth import Principal, require_scope
from enterprise_commerce.models import (
    AgenticEvalResult,
    CheckoutRequest,
    CheckoutResponse,
    NormalizedOffer,
    Product,
    QuoteRequest,
    QuoteResponse,
    ToolInvocation,
)
from enterprise_commerce.partners import PartnerRegistry
from enterprise_commerce.security import verify_webhook
from enterprise_commerce.services import CommerceOrchestrator

app = FastAPI(title="Enterprise Agentic Commerce Platform", version="0.1.0")
orchestrator = CommerceOrchestrator()
partners = PartnerRegistry()
WEBHOOK_SECRET = "enterprise-demo-secret"
idempotency: dict[str, CheckoutResponse] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/catalog/products", response_model=list[Product])
def products(_: Principal = Depends(require_scope("catalog:read"))) -> list[Product]:
    return orchestrator.list_products()


@app.post("/v1/quotes", response_model=QuoteResponse)
def quote(request: QuoteRequest, principal: Principal = Depends(require_scope("quote:write"))) -> QuoteResponse:
    return orchestrator.quote(request, principal)


@app.post("/v1/orders", response_model=CheckoutResponse)
def order(
    request: CheckoutRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
    principal: Principal = Depends(require_scope("order:write")),
) -> CheckoutResponse:
    if idempotency_key in idempotency:
        return idempotency[idempotency_key]
    response = orchestrator.checkout(request, principal)
    idempotency[idempotency_key] = response
    return response


@app.post("/v1/partners/{partner_id}/normalize-offer", response_model=NormalizedOffer)
def normalize_partner_offer(
    partner_id: str,
    payload: dict[str, Any],
    _: Principal = Depends(require_scope("partner:write")),
) -> NormalizedOffer:
    try:
        return partners.adapter_for(partner_id).normalize_offer(payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown partner") from exc


@app.post("/v1/webhooks/{partner_id}")
async def webhook(
    partner_id: str,
    request: Request,
    x_partner_signature: str = Header(...),
) -> dict[str, str]:
    body = await request.body()
    if not verify_webhook(WEBHOOK_SECRET, body, x_partner_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    return {"status": "accepted", "partner_id": partner_id}


@app.get("/mcp/tools")
def tools(_: Principal = Depends(require_scope("tools:invoke"))) -> dict[str, list[dict[str, Any]]]:
    return {
        "tools": [
            {"name": "catalog.search", "description": "Search product catalog.", "side_effects": "none"},
            {"name": "commerce.quote", "description": "Create a non-binding quote.", "side_effects": "none"},
            {"name": "commerce.checkout", "description": "Approved checkout.", "side_effects": "external_payment"},
        ]
    }


@app.post("/mcp/invoke")
def invoke_tool(
    invocation: ToolInvocation,
    principal: Principal = Depends(require_scope("tools:invoke")),
) -> dict[str, Any]:
    eval_result = evaluate_tool_call("tool invocation", invocation)
    if not eval_result.accepted:
        raise HTTPException(status_code=422, detail=eval_result.model_dump())
    if invocation.name == "commerce.quote":
        result = orchestrator.quote(QuoteRequest.model_validate(invocation.arguments), principal)
        return {"tool": invocation.name, "result": result.model_dump(mode="json")}
    if invocation.name == "catalog.search":
        query = invocation.arguments["query"].lower()
        matches = [product for product in orchestrator.list_products() if query in product.title.lower() or query in product.sku]
        return {"tool": invocation.name, "result": [product.model_dump(mode="json") for product in matches]}
    raise HTTPException(status_code=403, detail="Checkout tool requires direct order API and approval workflow")


@app.post("/v1/quality/agentic-eval", response_model=AgenticEvalResult)
def agentic_eval(prompt: str, invocation: ToolInvocation) -> AgenticEvalResult:
    return evaluate_tool_call(prompt, invocation)

