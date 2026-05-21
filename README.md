# Enterprise Agentic Commerce Platform

Flagship portfolio project for the Agentic AI API Developer role.

This project combines all JD skills into one production-shaped backend:

- Secure, versioned RESTful commerce APIs
- Auth scopes, tenant checks, and idempotency
- API orchestration across catalog, inventory, pricing, payment, fulfillment, partner adapters, and mandate validation
- MCP-style tool server shim for agentic workflows
- Third-party partner adapters with UCP-like normalized commerce objects
- AP2-inspired checkout mandate validation
- Webhook signature verification
- Agentic eval/quality gate harness
- API lifecycle and pod delivery docs
- GitHub Actions CI

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn enterprise_commerce.main:app --reload --app-dir src
```

## Demo Tokens

- `Bearer admin-token`: all scopes
- `Bearer partner-token`: `catalog:read quote:write order:write tools:invoke partner:write`
- `Bearer analyst-token`: `catalog:read quote:write`

## Main Endpoints

- `GET /health`
- `GET /v1/catalog/products`
- `POST /v1/quotes`
- `POST /v1/orders`
- `POST /v1/partners/{partner_id}/normalize-offer`
- `POST /v1/webhooks/{partner_id}`
- `GET /mcp/tools`
- `POST /mcp/invoke`
- `POST /v1/quality/agentic-eval`

