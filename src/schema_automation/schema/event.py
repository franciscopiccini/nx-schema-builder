"""Builder para schemas de Event (ej. Hot Sale, campañas promocionales)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..config import default_price_valid_until
from ..models import SchemaContext
from .base import (
    append_brand_organization,
    append_organization,
    build_faq_page,
    build_offer_node,
    build_webpage_node,
    organization_reference,
    resolve_organization,
)


def build_event_graph(
    ctx: SchemaContext,
    event_defaults: Optional[Dict[str, Any]] = None,
    **_,
) -> List[Dict[str, Any]]:
    """Construye el grafo JSON-LD para un evento (ej. Hot Sale, campaña promocional)."""
    graph: List[Dict[str, Any]] = []
    added_orgs: set = set()
    cfg = event_defaults or {}

    organizer_cfg = cfg.get("organizer") or {}
    organizer_org = resolve_organization(organizer_cfg, "naranja_x")

    event_name = cfg.get("event_name", ctx.name)
    event_status = cfg.get("event_status", "https://schema.org/EventScheduled")
    attendance_mode = cfg.get(
        "event_attendance_mode", "https://schema.org/OnlineEventAttendanceMode"
    )

    offer_id = f"{ctx.page_url}#Offer"

    event_node: Dict[str, Any] = {
        "@type": "Event",
        "@id": f"{ctx.page_url}#Event",
        "name": event_name,
        "description": ctx.description,
        "url": ctx.page_url,
        "eventStatus": event_status,
        "eventAttendanceMode": attendance_mode,
        "location": {
            "@type": "VirtualLocation",
            "url": ctx.page_url,
        },
        "organizer": organization_reference(organizer_org),
        "offers": {"@id": offer_id},
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ctx.page_url}#WebPage"},
    }

    if ctx.image_url:
        event_node["image"] = ctx.image_url

    # startDate es el único campo que Google exige siempre en Event. Sin él, la
    # página se reporta en Search Console como "markup con errores" y el Event no
    # se elige para resultados enriquecidos. No hay default razonable: la fecha
    # depende de la campaña, así que se exige al caller en lugar de inventarla.
    start_date = cfg.get("start_date")
    if not start_date:
        raise ValueError(
            "event_defaults['start_date'] es obligatorio: Google exige startDate "
            "en Event (formato ISO 8601, ej. '2026-11-30T00:00:00-03:00')."
        )
    event_node["startDate"] = start_date

    end_date = cfg.get("end_date")
    if end_date:
        event_node["endDate"] = end_date

    graph.append(event_node)

    offer_cfg = cfg.get("offer") or {}
    price_valid_until = offer_cfg.get("price_valid_until") or default_price_valid_until()
    offer_price = str(offer_cfg.get("price", "0") or "0")

    offer = build_offer_node(
        ctx.page_url,
        offer_id,
        {
            "name": event_name,
            "priceCurrency": offer_cfg.get("price_currency", "ARS"),
            "price": offer_price,
            "availability": offer_cfg.get("availability", "https://schema.org/InStock"),
            "validFrom": offer_cfg.get("valid_from", start_date) or "",
            "validThrough": offer_cfg.get("valid_through", end_date) or "",
            "url": ctx.page_url,
            "priceValidUntil": price_valid_until,
        },
    )
    graph.append(offer)

    faq_page = build_faq_page(ctx.page_url, ctx.faqs, f"{ctx.page_url}#FAQPage")
    if faq_page:
        graph.append(faq_page)

    graph.append(build_webpage_node(ctx))

    append_organization(graph, organizer_org, added_orgs)
    append_brand_organization(graph, added_orgs)

    return graph
