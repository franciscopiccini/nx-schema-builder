"""Builder para schemas de InvestmentOrDeposit."""

from __future__ import annotations

import re
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from ..config import INVESTMENT_OR_DEPOSIT_DEFAULTS, default_price_valid_until
from ..models import SchemaContext
from .base import (
    append_brand_organization,
    append_organization,
    build_faq_page,
    build_offer_node,
    build_product_node,
    build_webpage_node,
    deep_merge,
    resolve_organization,
)


def build_investment_or_deposit_graph(
    ctx: SchemaContext,
    investment_defaults: Optional[Dict[str, Any]] = None,
    **_,
) -> List[Dict[str, Any]]:
    """Construye el grafo JSON-LD para una inversión o depósito."""
    graph: List[Dict[str, Any]] = []
    added_orgs: set = set()
    today = date.today()
    defaults = INVESTMENT_OR_DEPOSIT_DEFAULTS
    overrides = investment_defaults or {}

    area_served = overrides.get("area_served", defaults.get("area_served", "AR"))

    base_globals = defaults.get("globals", {})
    override_globals = overrides.get("globals", {})
    combined_globals = {**base_globals, **override_globals}

    provider_defaults = defaults.get("provider", {})
    provider_overrides = overrides.get("provider", {})
    provider_cfg = deep_merge(provider_defaults, provider_overrides)
    provider = resolve_organization(provider_cfg, provider_defaults.get("org_key", "naranja_x"))

    investment_defaults_cfg = defaults.get("investment", {})
    investment_overrides = overrides.get("investment", {})

    investment_types = investment_overrides.get("types", investment_defaults_cfg.get("types", ["InvestmentOrDeposit"]))
    if isinstance(investment_types, str):
        investment_types = [investment_types]

    investment_id_suffix = investment_overrides.get("id_suffix", investment_defaults_cfg.get("id_suffix", "#investment"))
    investment_id = investment_overrides.get("id") or f"{ctx.page_url}{investment_id_suffix}"
    investment_alternate_name = investment_overrides.get(
        "alternate_name", investment_defaults_cfg.get("alternate_name")
    )
    investment_service_type = investment_overrides.get("service_type", investment_defaults_cfg.get("service_type"))
    investment_audience = investment_overrides.get("audience", investment_defaults_cfg.get("audience"))

    investment_identifier = overrides.get("identifier", investment_overrides.get("identifier"))
    if not investment_identifier:
        slug = re.sub(r"[^0-9A-Za-z]+", "-", ctx.name).strip("-")
        investment_identifier = slug or None

    interest_rate_defaults = investment_defaults_cfg.get("interest_rate", {})
    interest_rate_overrides = investment_overrides.get("interest_rate", {})
    interest_rate_type = interest_rate_overrides.get("type", interest_rate_defaults.get("type", "QuantitativeValue"))
    interest_rate_unit = interest_rate_overrides.get("unit_text", interest_rate_defaults.get("unit_text", "TNA"))
    default_rate_value = interest_rate_defaults.get("value", combined_globals.get("interest_rate", ""))
    interest_rate_value = interest_rate_overrides.get("value", default_rate_value)

    offer_defaults_cfg = defaults.get("offer", {})
    offer_overrides = overrides.get("offer", {})
    offer_id_suffix = offer_overrides.get("id_suffix", offer_defaults_cfg.get("id_suffix", "#offer"))
    offer_id = offer_overrides.get("id") or f"{ctx.page_url}{offer_id_suffix}"
    offer_price_currency = offer_overrides.get("price_currency", offer_defaults_cfg.get("price_currency", "ARS"))
    offer_area_served = offer_overrides.get("area_served", offer_defaults_cfg.get("area_served", area_served))
    offer_eligible_region = offer_overrides.get(
        "eligible_region", offer_defaults_cfg.get("eligible_region", area_served)
    )
    offer_availability = offer_overrides.get(
        "availability", offer_defaults_cfg.get("availability", "https://schema.org/InStock")
    )

    valid_from = offer_overrides.get("valid_from")
    if not valid_from:
        offset = offer_defaults_cfg.get("valid_from_offset", 0)
        valid_from = (today + timedelta(days=offset)).isoformat()
    valid_through = offer_overrides.get("valid_through")
    if not valid_through:
        offset = offer_defaults_cfg.get("valid_through_offset", 0)
        valid_through = (today + timedelta(days=offset)).isoformat()

    offer_name = offer_overrides.get("name", ctx.name or investment_overrides.get("name", ctx.name))
    offer_duration = offer_overrides.get("eligible_duration", combined_globals.get("duration", "")) or ""

    product_defaults_cfg = defaults.get("product", {})
    product_overrides = overrides.get("product", {})
    product_id_suffix = product_overrides.get("id_suffix", product_defaults_cfg.get("id_suffix", "#product"))
    product_id = product_overrides.get("id") or f"{ctx.page_url}{product_id_suffix}"

    faq_id_suffix = overrides.get("faq_id_suffix", defaults.get("faq_id_suffix", "#FAQPage"))
    faq_id = f"{ctx.page_url}{faq_id_suffix}"

    investment_node: Dict[str, Any] = {
        "@type": investment_types,
        "@id": investment_id,
        "name": ctx.name,
        "description": ctx.description,
        "areaServed": area_served,
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ctx.page_url}#WebPage"},
        "provider": provider,
        "offers": {"@id": offer_id},
        "interestRate": {
            "@type": interest_rate_type,
            "unitText": interest_rate_unit,
        },
    }

    if investment_alternate_name:
        investment_node["alternateName"] = investment_alternate_name
    if investment_service_type:
        investment_node["serviceType"] = investment_service_type
    if investment_audience:
        investment_node["audience"] = investment_audience
    if ctx.image_url:
        investment_node["image"] = ctx.image_url
    if investment_identifier:
        investment_node["identifier"] = investment_identifier

    if interest_rate_value not in (None, ""):
        investment_node["interestRate"]["value"] = interest_rate_value

    graph.append(investment_node)

    append_organization(graph, provider, added_orgs)
    append_brand_organization(graph, added_orgs)

    price_valid_until = default_price_valid_until()

    offer = build_offer_node(
        ctx.page_url,
        offer_id,
        {
            "name": offer_name,
            "price": offer_overrides.get("price", offer_defaults_cfg.get("price", "0")) or "0",
            "priceCurrency": offer_price_currency,
            "areaServed": offer_area_served,
            "eligibleRegion": offer_eligible_region,
            "availability": offer_availability,
            "validFrom": valid_from,
            "validThrough": valid_through,
            "priceValidUntil": price_valid_until,
            "eligibleDuration": offer_duration,
        },
    )
    graph.append(offer)

    product = build_product_node(
        ctx.page_url,
        product_id,
        ctx.name,
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
