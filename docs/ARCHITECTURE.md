# Architecture

```text
Partner / Agent / API Consumer
          |
          v
FastAPI REST + MCP Tool Shim
          |
          v
Commerce Orchestrator
          |
          +-- Catalog/Pricing/Inventory
          +-- Payment Authorization
          +-- Fulfillment
          +-- Partner Adapters
          +-- AP2-style Mandate Validation
          +-- Agentic Quality Evaluator
```

## Design Highlights

- REST endpoints are the deterministic system of record.
- MCP tools expose narrow agent-facing capabilities.
- Partner adapters normalize third-party and UCP-like payloads.
- Checkout requires idempotency and mandate validation.
- Agentic evals block unsafe tool calls before side effects.

