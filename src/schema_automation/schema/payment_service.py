"""Builder para schemas de PaymentService."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Any, Dict, List, Optional

from ..config import PAYMENT_SERVICE_DEFAULTS, default_price_valid_until
from ..models import SchemaContext
from .base import (
    append_brand_organization,
    append_organization,
    build_faq_page,
    build_offer_node,
    build_product_node,
    build_webpage_node,
    deep_merge,
    organization_reference,
    resolve_organization,
)


def build_payment_service_graph(
    ctx: SchemaContext,
    payment_service_defaults: Optional[Dict[str, Any]] = None,
    price_spec: Optional[Dict[str, Any]] = None,
    **_,
) -> List[Dict[str, Any]]:
    """Construye el grafo JSON-LD para un servicio de pago."""
    graph: List[Dict[str, Any]] = []
    added_orgs: set = set()
    today = date.today()
    next_year_end = date(today.year + 1, 12, 31)

    cfg = deep_merge(PAYMENT_SERVICE_DEFAULTS, payment_service_defaults or {})
    area_served = deepcopy(cfg.get("area_served", {"@type": "Country", "name": "Argentina"}))
    provider = resolve_organization(cfg.get("provider"), PAYMENT_SERVICE_DEFAULTS["provider"]["org_key"])

    service_node: Dict[str, Any] = {
        "@type": "PaymentService",
        "@id": f"{ctx.page_url}#PaymentService",
        "name": ctx.name,
        "description": ctx.description,
        "areaServed": deepcopy(area_served),
        "provider": organization_reference(provider),
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ctx.page_url}#WebPage"},
        "offers": {"@id": f"{ctx.page_url}#Offer"},
    }
    if ctx.image_url:
        service_node["image"] = ctx.image_url
    graph.append(service_node)

    offer_cfg = cfg.get("offer", {})
    valid_from = offer_cfg.get("valid_from", today.isoformat())
    valid_through = offer_cfg.get("valid_through", next_year_end.isoformat())
    availability_starts = offer_cfg.get("availability_starts", valid_from)
    price_valid_until = offer_cfg.get("price_valid_until") or default_price_valid_until()

    offer = build_offer_node(
        ctx.page_url,
        f"{ctx.page_url}#Offer",
        {
            "priceCurrency": offer_cfg.get("price_currency", "ARS"),
            "areaServed": deepcopy(area_served),
            "validFrom": valid_from,
            "validThrough": valid_through,
            "availability": offer_cfg.get("availability", "https://schema.org/InStock"),
            "availabilityStarts": availability_starts,
            "eligibleRegion": offer_cfg.get("eligible_region", "AR"),
            "priceValidUntil": price_valid_until,
            "price": offer_cfg.get("price", "0") or "0",
        },
    )
    graph.append(offer)

    product = build_product_node(
        ctx.page_url,
        f"{ctx.page_url}#Product",
        ctx.name,
        ctx.image_url,
        ctx.aggregate_rating,
        description=ctx.description,
        extra={"url": ctx.page_url, "offers": {"@id": f"{ctx.page_url}#Offer"}},
    )
    graph.append(product)

    faq_page = build_faq_page(ctx.page_url, ctx.faqs, f"{ctx.page_url}#FAQPage")
    if faq_page:
        graph.append(faq_page)

    graph.append(build_webpage_node(ctx))

    append_organization(graph, provider, added_orgs)
    append_brand_organization(graph, added_orgs)

    return graph
