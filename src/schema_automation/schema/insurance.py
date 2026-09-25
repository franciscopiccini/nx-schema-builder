"""Builder para schemas de InsuranceAgency."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from ..config import INSURANCE_AGENCY_DEFAULTS, default_price_valid_until
from ..models import SchemaContext
from .base import (
    append_brand_organization,
    append_organization,
    build_faq_page,
    build_offer_node,
    build_product_node,
    build_webpage_node,
    resolve_organization,
)


def build_insurance_agency_graph(
    ctx: SchemaContext,
    insurance_defaults: Optional[Dict[str, Any]] = None,
    **_,
) -> List[Dict[str, Any]]:
    """Construye el grafo JSON-LD para una agencia de seguros."""
    graph: List[Dict[str, Any]] = []
    added_orgs: set = set()
    today = date.today()
    next_year_end = date(today.year + 1, 12, 31)

    defaults = INSURANCE_AGENCY_DEFAULTS
    overrides = insurance_defaults or {}

    agency_base = defaults.get("agency", {})
    agency_overrides = overrides.get("agency", {})
    agency_identifier = {
        **agency_base.get("identifier", {}),
        **agency_overrides.get("identifier", {}),
    }
    if not agency_identifier.get("propertyID") or not agency_identifier.get("value"):
        agency_identifier = None
    agency_logo = {**agency_base.get("logo", {}), **agency_overrides.get("logo", {})}
    if not agency_logo.get("url") and ctx.image_url:
        agency_logo["url"] = ctx.image_url

    agency_same_as = agency_overrides.get("same_as", agency_base.get("same_as", []))
    if isinstance(agency_same_as, str):
        agency_same_as = [agency_same_as]

    area_served = overrides.get("area_served", agency_base.get("area_served", "AR"))
    addresses = overrides.get("addresses", agency_base.get("addresses"))

    agency_id_suffix = agency_overrides.get("id_suffix", agency_base.get("id_suffix", "#insurance-agency"))
    agency_id = agency_overrides.get("id") or f"{ctx.page_url}{agency_id_suffix}"

    agency_node: Dict[str, Any] = {
        "@type": "InsuranceAgency",
        "@id": agency_id,
        "name": ctx.name,
        "description": ctx.description,
        "areaServed": area_served,
        "url": ctx.page_url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ctx.page_url}#WebPage"},
    }
    if agency_identifier:
        agency_node["identifier"] = agency_identifier
    if agency_logo:
        agency_node["logo"] = agency_logo
    if addresses:
        agency_node["address"] = addresses
    if agency_same_as:
        agency_node["sameAs"] = agency_same_as

    graph.append(agency_node)

    offer_defaults = defaults.get("offer", {})
    offer_overrides = overrides.get("offer", {})
    offer_id_suffix = offer_overrides.get("id_suffix", offer_defaults.get("id_suffix", "#offer"))
    offer_id = offer_overrides.get("id") or f"{ctx.page_url}{offer_id_suffix}"
    offer_name = offer_overrides.get("name", offer_defaults.get("name", ctx.name))
    offer_price_currency = offer_overrides.get("price_currency", offer_defaults.get("price_currency", "ARS"))
    offer_availability = offer_overrides.get("availability", offer_defaults.get("availability", "https://schema.org/InStock"))
    offer_area_served = offer_overrides.get("area_served", offer_defaults.get("area_served", "AR"))
    offer_eligible_region = offer_overrides.get("eligible_region", offer_defaults.get("eligible_region", "AR"))
    offer_price = offer_overrides.get("price", offer_defaults.get("price", "0")) or "0"
    price_valid_until = offer_overrides.get("price_valid_until") or default_price_valid_until()

    offer = build_offer_node(
        ctx.page_url,
        offer_id,
        {
            "name": offer_name,
            "priceCurrency": offer_price_currency,
            "availability": offer_availability,
            "validFrom": offer_overrides.get("valid_from", today.isoformat()),
            "areaServed": offer_area_served,
            "eligibleRegion": offer_eligible_region,
            "priceValidUntil": price_valid_until,
            "price": offer_price,
        },
    )
    graph.append(offer)

    product_defaults = defaults.get("product", {})
    product_overrides = overrides.get("product", {})
    product_id_suffix = product_overrides.get("id_suffix", product_defaults.get("id_suffix", "#producto"))
    product_id = product_overrides.get("id") or f"{ctx.page_url}{product_id_suffix}"

    product = build_product_node(
        ctx.page_url,
        product_id,
        ctx.name,
        ctx.image_url,
        ctx.aggregate_rating,
        description=ctx.description,
        extra={"url": ctx.page_url, "offers": {"@id": offer_id}},
    )
    product_category = product_overrides.get("category", product_defaults.get("category"))
    if product_category:
        product["category"] = product_category
    graph.append(product)

    faq_page = build_faq_page(ctx.page_url, ctx.faqs, f"{ctx.page_url}#FAQPage")
    if faq_page:
        graph.append(faq_page)

    graph.append(build_webpage_node(ctx))

    # No se emite una Organization extra para la agencia: resolve_organization
    # no encuentra `agency_id` en ORGANIZATIONS y devolvía la marca con el @id
    # pisado, duplicando el @id del nodo InsuranceAgency de arriba. La marca se
    # emite una sola vez con su @id propio.
    append_brand_organization(graph, added_orgs)

    return graph
