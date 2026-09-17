"""Builder para schemas de FinancialProduct."""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ..config import (
    FINANCIAL_PRODUCT_DEFAULTS,
    default_price_valid_until,
)
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


def build_financial_product_graph(
    ctx: SchemaContext,
    financial_product_defaults: Optional[Dict[str, Any]] = None,
    **_,
) -> List[Dict[str, Any]]:
    """Construye el grafo JSON-LD para un producto financiero genérico."""
    graph: List[Dict[str, Any]] = []
    added_orgs: set = set()
    today = date.today()
    defaults = FINANCIAL_PRODUCT_DEFAULTS
    overrides = financial_product_defaults or {}

    area_served = overrides.get("area_served", defaults.get("area_served", "AR"))

    provider_defaults = defaults.get("provider", {})
    provider_overrides = overrides.get("provider", {})
    provider_cfg = deep_merge(provider_defaults, provider_overrides)
    provider = resolve_organization(provider_cfg, provider_defaults.get("org_key", "tarjeta_naranja"))

    rates = overrides.get("rates", {})
    rate_parts = []
    for code, value in (rates or {}).items():
        if isinstance(value, (int, float)):
            formatted = f"{value:.2f}".rstrip("0").rstrip(".")
        else:
            formatted = str(value)
        if formatted and not formatted.endswith("%"):
            formatted = f"{formatted} %"
        rate_parts.append(f"{code} {formatted}".strip())
    rates_text = ", ".join([p for p in rate_parts if p])

    offer_defaults = defaults.get("offer", {})
    offer_overrides = overrides.get("offer", {})
    valid_from = offer_overrides.get("valid_from")
    if not valid_from:
        offset = offer_defaults.get("valid_from_offset", 0)
        valid_from = (today + timedelta(days=offset)).isoformat()
    valid_through = offer_overrides.get("valid_through")
    if not valid_through:
        offset = offer_defaults.get("valid_through_offset", 30)
        valid_through = (today + timedelta(days=offset)).isoformat()
    price_currency = offer_overrides.get("price_currency", offer_defaults.get("price_currency", "ARS"))
    billing_increment = offer_overrides.get("billing_increment", offer_defaults.get("billing_increment", "1"))
    min_price = offer_overrides.get("min_price", offer_defaults.get("min_price", "0"))
    offer_area_served = offer_overrides.get("area_served", offer_defaults.get("area_served", area_served))
    description_template = offer_overrides.get(
        "description_template", offer_defaults.get("description_template", "Características financieras: {rates_text}.")
    )
    offer_description = offer_overrides.get("description")
    if not offer_description and description_template and rates_text:
        offer_description = description_template.format(rates_text=rates_text)

    identifier = overrides.get("identifier", defaults.get("identifier"))
    if not identifier:
        slug = re.sub(r"[^0-9A-Za-z]+", "-", ctx.name).strip("-")
        identifier = slug or None

    product_defaults = defaults.get("product", {})
    product_overrides = overrides.get("product", {})
    product_id_suffix = product_overrides.get("id_suffix", product_defaults.get("id_suffix", "#Product"))
    product_id = product_overrides.get("id") or f"{ctx.page_url}{product_id_suffix}"
    product_name_value = product_overrides.get("name", product_defaults.get("name", ctx.name))

    faq_id_suffix = overrides.get("faq_id_suffix", defaults.get("faq_id_suffix", "#FAQPage"))
    faq_id = f"{ctx.page_url}{faq_id_suffix}"

    offer_id = f"{ctx.page_url}#Offer"

    financial_product = {
        "@type": "FinancialProduct",
        "@id": f"{ctx.page_url}#FinancialProduct",
        "name": ctx.name,
        "description": ctx.description,
        "areaServed": area_served,
        "provider": organization_reference(provider),
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ctx.page_url}#WebPage"},
        "offers": {"@id": offer_id},
    }
    if ctx.image_url:
        financial_product["image"] = ctx.image_url
    if identifier:
        financial_product["identifier"] = identifier
    graph.append(financial_product)

    append_organization(graph, provider, added_orgs)
    append_brand_organization(graph, added_orgs)

    price_valid_until = default_price_valid_until()

    price_spec = {
        "@type": "UnitPriceSpecification",
        "billingIncrement": billing_increment,
        "price": min_price,
        "priceCurrency": price_currency,
    }
    if offer_description:
        price_spec["description"] = offer_description

    offer = build_offer_node(
        ctx.page_url,
        offer_id,
        {
            "priceCurrency": price_currency,
            "areaServed": offer_area_served,
            "validFrom": valid_from,
            "validThrough": valid_through,
            "itemOffered": {"@id": product_id},
            "priceValidUntil": price_valid_until,
            "price": min_price,
            "priceSpecification": price_spec,
        },
    )
    graph.append(offer)

    product = build_product_node(
        ctx.page_url,
        product_id,
        product_name_value,
        ctx.image_url,
        ctx.aggregate_rating,
        description=ctx.description,
        extra={"url": ctx.page_url, "offers": {"@id": offer_id}},
    )
    graph.append(product)

    faq_page = build_faq_page(ctx.page_url, ctx.faqs, faq_id)
    if faq_page:
        graph.append(faq_page)

    graph.append(build_webpage_node(ctx))

    return graph
