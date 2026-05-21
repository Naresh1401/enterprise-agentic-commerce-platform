from fastapi.testclient import TestClient

from enterprise_commerce.main import WEBHOOK_SECRET, app
from enterprise_commerce.security import sign_webhook

client = TestClient(app)


def auth(token: str = "partner-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_catalog_requires_auth() -> None:
    response = client.get("/v1/catalog/products")
    assert response.status_code == 401


def test_quote_orchestration() -> None:
    response = client.post(
        "/v1/quotes",
        headers=auth(),
        json={"customer_id": "cust_1", "items": [{"sku": "coffee", "quantity": 2}], "destination_zip": "45202"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == "32.92"


def test_checkout_requires_trusted_mandate_and_idempotency() -> None:
    payload = {
        "customer_id": "cust_1",
        "items": [{"sku": "coffee", "quantity": 1}],
        "destination_zip": "45202",
        "payment_token": "tok_12345678",
        "mandate": {
            "mandate_id": "mandate_1",
            "shopper_id": "shopper_1",
            "checkout_hash": "abcdef1234567890",
            "max_total": "20.00",
            "signed_by_trusted_surface": True,
        },
    }
    headers = {**auth(), "Idempotency-Key": "same-checkout"}
    first = client.post("/v1/orders", headers=headers, json=payload)
    second = client.post("/v1/orders", headers=headers, json=payload)
    assert first.status_code == 200
    assert first.json()["order_id"] == second.json()["order_id"]


def test_checkout_rejects_untrusted_mandate() -> None:
    payload = {
        "customer_id": "cust_1",
        "items": [{"sku": "coffee", "quantity": 1}],
        "destination_zip": "45202",
        "payment_token": "tok_12345678",
        "mandate": {
            "mandate_id": "mandate_1",
            "shopper_id": "shopper_1",
            "checkout_hash": "abcdef1234567890",
            "max_total": "20.00",
            "signed_by_trusted_surface": False,
        },
    }
    response = client.post("/v1/orders", headers={**auth(), "Idempotency-Key": "bad-mandate"}, json=payload)
    assert response.status_code == 403


def test_ucp_like_partner_adapter_endpoint() -> None:
    response = client.post(
        "/v1/partners/ucp_like/normalize-offer",
        headers=auth(),
        json={
            "commerceObjectId": "obj_1",
            "merchantSku": "coffee",
            "displayName": "Cincinnati Coffee",
            "agentSurface": "agent",
            "offers": [{"price": {"amount": "12.99"}, "availability": "in_stock"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["attributes"]["protocol"] == "ucp_like"


def test_webhook_signature_verification() -> None:
    body = b'{"event":"offer.updated"}'
    response = client.post(
        "/v1/webhooks/ucp_like",
        content=body,
        headers={"X-Partner-Signature": sign_webhook(WEBHOOK_SECRET, body)},
    )
    assert response.status_code == 200


def test_mcp_quote_tool() -> None:
    response = client.post(
        "/mcp/invoke",
        headers=auth(),
        json={"name": "commerce.quote", "arguments": {"customer_id": "cust_1", "items": [{"sku": "mug", "quantity": 1}], "destination_zip": "45202"}},
    )
    assert response.status_code == 200
    assert response.json()["result"]["total"] == "15.20"


def test_agentic_eval_blocks_checkout_without_human_approval() -> None:
    response = client.post(
        "/v1/quality/agentic-eval?prompt=buy%20this",
        json={
            "name": "commerce.checkout",
            "arguments": {
                "customer_id": "cust_1",
                "items": [{"sku": "coffee", "quantity": 1}],
                "destination_zip": "45202",
                "payment_token": "tok_12345678",
                "mandate": {"mandate_id": "m1"},
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["accepted"] is False
    assert "human approval required" in response.json()["reasons"]

