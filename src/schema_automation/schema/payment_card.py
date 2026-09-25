"""Builder para schemas de PaymentCard."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from ..config import default_price_valid_until
from ..models import SchemaContext
from .base import (
    append_brand_organization,
    append_organization,
    build_faq_page,
    build_offer_node,
    build_product_node,
    build_webpage_node,
    organization_reference,
    resolve_organization,
)


def build_payment_card_graph(ctx: SchemaContext, **_) -> List[Dict[str, Any]]:
    """Construye el grafo JSON-LD para una tarjeta de pago."""
    graph: List[Dict[str, Any]] = []
    added_orgs: set = set()

    offer_id = f"{ctx.page_url}#Offer"

    payment_card: Dict[str, Any] = {
        "@type": "PaymentCard",
        "@id": f"{ctx.page_url}#PaymentCard",
        "url": ctx.page_url,
        "name": ctx.name,
        "description": ctx.description,
        "areaServed": "AR",
        "provider": [organization_reference("tarjeta_naranja")],
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ctx.page_url}#WebPage"},
        "offers": {"@id": offer_id},
    }
    if ctx.image_url:
        payment_card["image"] = {
            "@type": "ImageObject",
            "@id": f"{ctx.page_url}#PaymentCardImage",
            "url": ctx.image_url,
        }
    graph.append(payment_card)

    price_valid_until = default_price_valid_until()

    offer = build_offer_node(
        ctx.page_url,
        offer_id,
        {
            "name": ctx.name,
            "price": "0",
            "priceCurrency": "ARS",
            "availability": "https://schema.org/InStock",
            "validFrom": date.today().isoformat(),
            "areaServed": "AR",
            "priceValidUntil": price_valid_until,
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
        extra={"url": ctx.page_url, "offers": {"@id": offer_id}},
    )
    graph.append(product)

    faq_page = build_faq_page(ctx.page_url, ctx.faqs, f"{ctx.page_url}#FAQPage")
    if faq_page:
        graph.append(faq_page)

    graph.append(build_webpage_node(ctx))

    append_organization(graph, resolve_organization({}, "tarjeta_naranja"), added_orgs)
    append_brand_organization(graph, added_orgs)

    return graph
