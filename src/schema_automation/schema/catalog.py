"""Builder para OfferCatalog."""

from __future__ import annotations

import re
import unicodedata
from copy import deepcopy
from typing import Any, Dict, Optional, Tuple

from ..config import OFFER_CATALOGS, ORGANIZATIONS, default_price_valid_until


def build_offer_catalog_node(
    page_url: str, catalog_key: str
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Construye un nodo OfferCatalog con sus ofertas."""
    catalog = OFFER_CATALOGS.get(catalog_key)
    if not catalog:
        return None, None

    # Se translitera a ASCII antes de slugificar: sin esto "Catálogo" queda
    # como "Cat-logo", porque la vocal acentuada no matchea [0-9A-Za-z].
    ascii_name = (
        unicodedata.normalize("NFKD", str(catalog["name"]))
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    node_id_suffix = re.sub(r"[^0-9A-Za-z]+", "-", ascii_name).strip("-") or catalog_key
    node_id = f"{page_url}#OfferCatalog{node_id_suffix}"

    item_list = []
    for idx, item in enumerate(catalog.get("items", []), start=1):
        name = item.get("name")
        url = item.get("url")
        if not name or not url:
            continue
        offer_id = f"{node_id}-Offer{idx}"

        item_id_override = item.get("item_id") or item.get("@id")
        id_suffix = item.get("id_suffix")
        item_type = item.get("item_type", "Product")

        if item_id_override:
            item_offered: Dict[str, Any] = {"@id": item_id_override}
        elif id_suffix and url:
            item_offered = {"@id": f"{url}{id_suffix}"}
        else:
            item_offered = {"@type": item_type, "name": name}
            if url:
                item_offered["url"] = url

        offer_props = item.get("offer", {}) if isinstance(item.get("offer"), dict) else {}
        offer_price = offer_props.get("price", catalog.get("default_price", "0"))
        if offer_price in (None, ""):
            offer_price = "0"
        offer_currency = (
            offer_props.get("priceCurrency")
            or offer_props.get("price_currency")
            or catalog.get("price_currency", "ARS")
        )
        offer_availability = (
            offer_props.get("availability") or catalog.get("availability", "https://schema.org/InStock")
        )
        offer_price_valid_until = (
            offer_props.get("priceValidUntil")
            or offer_props.get("price_valid_until")
            or catalog.get("price_valid_until")
        )
        if not offer_price_valid_until:
            offer_price_valid_until = default_price_valid_until()

        offer_item = {
            "@type": "Offer",
            "@id": offer_id,
            "name": name,
            "price": offer_price,
            "priceCurrency": offer_currency,
            "availability": offer_availability,
            "priceValidUntil": offer_price_valid_until,
            "itemOffered": item_offered,
            "url": url,
        }
        item_list.append(offer_item)

    if not item_list:
        return None, None

    catalog_node: Dict[str, Any] = {
        "@type": "OfferCatalog",
        "@id": node_id,
        "name": catalog["name"],
        "itemListElement": item_list,
    }

    provider_key = catalog.get("provider", "naranja_x")
    provider_org = ORGANIZATIONS.get(provider_key)

    return catalog_node, deepcopy(provider_org) if provider_org else None
