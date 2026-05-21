from decimal import Decimal
from typing import Any

from enterprise_commerce.models import NormalizedOffer


class PartnerAdapter:
    partner_id = "base"

    def normalize_offer(self, payload: dict[str, Any]) -> NormalizedOffer:
        raise NotImplementedError


class ShopifyLikeAdapter(PartnerAdapter):
    partner_id = "shopify_like"

    def normalize_offer(self, payload: dict[str, Any]) -> NormalizedOffer:
        variant = payload["variants"][0]
        return NormalizedOffer(
            partner_id=self.partner_id,
            sku=variant["sku"],
            title=payload["title"],
            price=Decimal(str(variant["price"])),
            availability="in_stock" if variant.get("inventory_quantity", 0) > 0 else "out_of_stock",
            source_ref=str(payload["id"]),
            attributes={"vendor": payload.get("vendor")},
        )


class UcpLikeAdapter(PartnerAdapter):
    partner_id = "ucp_like"

    def normalize_offer(self, payload: dict[str, Any]) -> NormalizedOffer:
        offer = payload["offers"][0]
        return NormalizedOffer(
            partner_id=self.partner_id,
            sku=payload["merchantSku"],
            title=payload["displayName"],
            price=Decimal(str(offer["price"]["amount"])),
            availability=offer.get("availability", "in_stock"),
            source_ref=payload["commerceObjectId"],
            attributes={"agent_surface": payload.get("agentSurface", "unknown"), "protocol": "ucp_like"},
        )


class PartnerRegistry:
    def __init__(self) -> None:
        self.adapters = {
            "shopify_like": ShopifyLikeAdapter(),
            "ucp_like": UcpLikeAdapter(),
        }

    def adapter_for(self, partner_id: str) -> PartnerAdapter:
        return self.adapters[partner_id]

    def ids(self) -> list[str]:
        return sorted(self.adapters)

