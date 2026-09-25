"""Funciones base y utilidades compartidas para la construcción de schemas."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from ..config import (
    DEFAULT_LANGUAGE,
    ORGANIZATIONS,
    PRODUCT_BRAND,
    WEBPAGE_DEFAULTS,
)
from ..models import SchemaContext


def deep_merge(base: Dict[str, Any], overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Combina recursivamente dos diccionarios, priorizando overrides."""
    result = deepcopy(base)
    if not overrides:
        return result
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def organization_reference(org_key_or_data: Any) -> Dict[str, str]:
    """Crea una referencia @id a una organización."""
    if isinstance(org_key_or_data, dict):
        return {"@id": org_key_or_data.get("@id")}
    return {"@id": ORGANIZATIONS[org_key_or_data]["@id"]}


def resolve_organization(config: Optional[Dict[str, Any]], default_key: str) -> Dict[str, Any]:
    """Resuelve y combina configuración de organización con defaults."""
    cfg = config or {}
    org_key = cfg.get("org_key") or default_key
    base = deepcopy(ORGANIZATIONS.get(org_key, ORGANIZATIONS[default_key]))
    org_id = cfg.get("id") or cfg.get("@id")
    if org_id:
        matched = next(
            (deepcopy(org) for org in ORGANIZATIONS.values() if org.get("@id") == org_id),
            None,
        )
        if matched:
            base = matched
    for key, value in cfg.items():
        if key in {"org_key", "overrides"}:
            continue
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key].update(value)
        else:
            base[key] = deepcopy(value)
    overrides = cfg.get("overrides")
    if overrides:
        for key, value in overrides.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                base[key].update(value)
            else:
                base[key] = deepcopy(value)
    return base


def append_organization(graph: List[Dict[str, Any]], org_data: Dict[str, Any], added_ids: set):
    """Agrega una organización al grafo evitando duplicados."""
    org_id = org_data.get("@id")
    if org_id and org_id in added_ids:
        return
    graph.append(org_data)
    if org_id:
        added_ids.add(org_id)


def append_brand_organization(graph: List[Dict[str, Any]], added_ids: set):
    """Garantiza que la marca (Naranja X) exista como nodo en el grafo.

    Las emisoras la referencian por @id vía parentOrganization/brand, y el
    WebPage vía publisher. Sin este nodo esas referencias quedan colgando y el
    consumidor no puede resolver la entidad que concentra los sameAs.
    """
    append_organization(graph, deepcopy(ORGANIZATIONS["naranja_x"]), added_ids)


def _faq_entities(faqs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Convierte FAQs a entidades Question/Answer de schema.org."""
    entities: List[Dict[str, Any]] = []
    for faq in faqs or []:
        question = faq.get("question", "").strip()
        answer = faq.get("answer", "").strip()
        if not question or not answer:
            continue
        entities.append(
            {
                "@type": "Question",
                "name": question,
                "acceptedAnswer": {"@type": "Answer", "text": answer},
            }
        )
    return entities


def build_faq_page(
    page_url: str,
    faqs: List[Dict[str, str]],
    node_id: str,
    extra: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Construye un nodo FAQPage si hay FAQs válidas."""
    entities = _faq_entities(faqs)
    if not entities:
        return None

    node: Dict[str, Any] = {
        "@type": "FAQPage",
        "@id": node_id,
        "inLanguage": DEFAULT_LANGUAGE,
        "mainEntity": entities,
    }
    if extra:
        node.update(extra)
    return node


def build_product_node(
    page_url: str,
    node_id: str,
    name: str,
    image_url: Optional[str],
    aggregate_rating: Optional[Dict[str, Any]],
    description: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Construye un nodo Product genérico."""
    node: Dict[str, Any] = {"@type": "Product", "@id": node_id, "name": name, "brand": deepcopy(PRODUCT_BRAND)}
    if image_url:
        node["image"] = image_url
    if aggregate_rating:
        node["aggregateRating"] = deepcopy(aggregate_rating)
    if description:
        node["description"] = description
    if extra:
        node.update(extra)
    return node


def build_offer_node(page_url: str, node_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Construye un nodo Offer genérico."""
    node: Dict[str, Any] = {"@type": "Offer", "@id": node_id, "url": data.get("url", page_url)}
    for key, value in data.items():
        if key == "url":
            continue
        node[key] = value
    return node


def build_webpage_node(ctx: SchemaContext, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Construye un nodo WebPage."""
    node = deepcopy(WEBPAGE_DEFAULTS)
    node["@id"] = f"{ctx.page_url}#WebPage"
    node["url"] = ctx.page_url
    node["name"] = ctx.name
    if ctx.description:
        node["description"] = ctx.description
    if extra:
        node.update(extra)
    return node
