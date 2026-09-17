"""Servicios de orquestación para construir los schemas completos."""

from __future__ import annotations

import logging
import re
from copy import deepcopy
from typing import Any, Dict, Optional

from ..config import TOPICAL_ENTITIES, TOPICAL_ENTITY_CHOICES
from ..extraction import extract_basic_meta, extract_body_text, extract_faqs
from ..extraction.html import ensure_soup
from ..infrastructure.http import fetch_html
from ..infrastructure.persistence import as_script_tag, save_outputs
from ..models import ExtractionResult, SchemaContext, SchemaRecord
from ..schema import SCHEMA_BUILDERS, build_offer_catalog_node
from ..validation import SchemaValidationResult, validate_schema

logger = logging.getLogger(__name__)


def _schema_type_key(schema_type: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", schema_type).lower().replace("-", "_").strip()


def _attach_topical_entity(
    graph_nodes: list, schema_key: str, topical_entity: Optional[str] = None
) -> None:
    """Adjunta la entidad temática (`about`) al nodo WebPage del grafo.

    `about`/`mentions` son propiedades exclusivas de CreativeWork, por eso solo
    se aplican a WebPage (nunca a Product/PaymentCard/etc.). No hace nada si el
    tipo no tiene entidad mapeada o si el grafo no incluye un nodo WebPage.

    `topical_entity` es una clave de TOPICAL_ENTITY_CHOICES que reemplaza al
    default del tipo, para las páginas donde el default es demasiado genérico
    (p. ej. una landing de débito bajo el tipo payment_card).
    """
    if topical_entity:
        entity = TOPICAL_ENTITY_CHOICES.get(topical_entity)
        if entity is None:
            raise ValueError(
                f"topical_entity '{topical_entity}' no existe. "
                f"Opciones: {', '.join(sorted(TOPICAL_ENTITY_CHOICES))}."
            )
    else:
        entity = TOPICAL_ENTITIES.get(schema_key)
    if not entity:
        return
    webpage = next(
        (
            node
            for node in graph_nodes
            if isinstance(node, dict) and node.get("@type") == "WebPage"
        ),
        None,
    )
    if webpage is None:
        return
    about = {"@type": "Thing", **deepcopy(entity)}
    existing = webpage.get("about")
    if existing is None:
        webpage["about"] = about
    elif isinstance(existing, list):
        if not any(item.get("@id") == about["@id"] for item in existing if isinstance(item, dict)):
            existing.append(about)
    elif isinstance(existing, dict):
        if existing.get("@id") != about["@id"]:
            webpage["about"] = [existing, about]


def build_schema_from_url(
    url: str,
    nombre: str,
    schema_type: str = "payment_card",
    *,
    price_spec: Optional[Dict[str, Any]] = None,
    bank_defaults: Optional[Dict[str, Any]] = None,
    payment_service_defaults: Optional[Dict[str, Any]] = None,
    insurance_defaults: Optional[Dict[str, Any]] = None,
    loan_defaults: Optional[Dict[str, Any]] = None,
    financial_product_defaults: Optional[Dict[str, Any]] = None,
    investment_defaults: Optional[Dict[str, Any]] = None,
    blog_defaults: Optional[Dict[str, Any]] = None,
    event_defaults: Optional[Dict[str, Any]] = None,
    offer_catalog_key: Optional[str] = None,
    aggregate_rating: Optional[Dict[str, Any]] = None,
    topical_entity: Optional[str] = None,
    validate: bool = False,
) -> SchemaRecord:
    """
    Construye un schema JSON-LD a partir de una URL.

    Args:
        url: URL de la página a procesar.
        nombre: Nombre legible del producto/servicio.
        schema_type: Tipo de schema a generar.
        price_spec: Especificaciones de precio opcionales.
        bank_defaults: Configuración para BankAccount.
        payment_service_defaults: Configuración para PaymentService.
        insurance_defaults: Configuración para InsuranceAgency.
        loan_defaults: Configuración para LoanOrCredit.
        financial_product_defaults: Configuración para FinancialProduct.
        investment_defaults: Configuración para InvestmentOrDeposit.
        blog_defaults: Configuración para BlogPosting.
        event_defaults: Configuración para Event. Requiere start_date (ISO 8601).
        offer_catalog_key: Clave del catálogo de ofertas a incluir.
        aggregate_rating: Rating agregado personalizado.
        topical_entity: Clave de TOPICAL_ENTITY_CHOICES para reemplazar la
            entidad `about` por defecto del tipo (ej. "tarjeta_debito").
        validate: Si True, valida el schema generado.

    Returns:
        SchemaRecord con los datos extraídos y el schema generado.

    Raises:
        ValueError: Si el schema_type no es válido.
        ValidationError: Si validate=True y el schema no es válido.
    """
    html, base_url, final_url = fetch_html(url)
    soup = ensure_soup(html)
    meta = extract_basic_meta(html, base_url=base_url, soup=soup)

    faqs = extract_faqs(soup)

    body_text = extract_body_text(soup)

    image_url = meta.get("image", "") or ""
    description_text = meta.get("description", "") or ""

    # Sin aggregateRating por defecto: solo se emite si el caller pasa uno
    # explícitamente, respaldado por reviews reales. Emitir un rating inventado
    # es structured data engañoso y expone el sitio a una acción manual.
    agg_rating = deepcopy(aggregate_rating) if aggregate_rating else None
    if agg_rating is not None:
        agg_rating.setdefault("@type", "AggregateRating")

    key = _schema_type_key(schema_type)
    builder = SCHEMA_BUILDERS.get(key)
    if builder is None:
        raise ValueError(f"schema_type desconocido: {schema_type}")

    context = SchemaContext(
        page_url=final_url,
        name=nombre,
        description=description_text,
        image_url=image_url or None,
        faqs=faqs,
        body_text=body_text or None,
        aggregate_rating=agg_rating,
    )

    graph_nodes = builder(
        context,
        price_spec=price_spec,
        bank_defaults=bank_defaults,
        payment_service_defaults=payment_service_defaults,
        insurance_defaults=insurance_defaults,
        loan_defaults=loan_defaults,
        financial_product_defaults=financial_product_defaults,
        investment_defaults=investment_defaults,
        blog_defaults=blog_defaults,
        event_defaults=event_defaults,
    )

    _attach_topical_entity(graph_nodes, key, topical_entity)

    if offer_catalog_key:
        catalog_node, provider_org = build_offer_catalog_node(context.page_url, offer_catalog_key)
        if catalog_node:
            graph_nodes.append(catalog_node)
            if provider_org and provider_org.get("@id"):
                existing_ids = {
                    node.get("@id")
                    for node in graph_nodes
                    if isinstance(node, Dict) and node.get("@id")
                }
                if provider_org["@id"] not in existing_ids:
                    graph_nodes.append(provider_org)

    schema_graph = {"@context": "https://schema.org", "@graph": graph_nodes}

    # Validar si se solicita
    if validate:
        validation_result = validate_schema(schema_graph)
        if not validation_result.is_valid:
            error_msgs = [str(e) for e in validation_result.errors[:5]]
            logger.warning(
                "Schema validation failed for %s: %s",
                final_url,
                "; ".join(error_msgs),
            )

    extracted = ExtractionResult(
        title=meta.get("title", ""),
        description=description_text,
        image=image_url,
        faqs=faqs,
        body_text=body_text,
    )

    return SchemaRecord(
        url=final_url,
        name=nombre,
        schema_type=schema_type,
        extracted=extracted,
        schema=schema_graph,
    )


def generate_schema(
    url: str,
    nombre: str,
    schema_type: str = "payment_card",
    *,
    price_spec: Optional[Dict[str, Any]] = None,
    bank_defaults: Optional[Dict[str, Any]] = None,
    payment_service_defaults: Optional[Dict[str, Any]] = None,
    insurance_defaults: Optional[Dict[str, Any]] = None,
    loan_defaults: Optional[Dict[str, Any]] = None,
    financial_product_defaults: Optional[Dict[str, Any]] = None,
    investment_defaults: Optional[Dict[str, Any]] = None,
    blog_defaults: Optional[Dict[str, Any]] = None,
    event_defaults: Optional[Dict[str, Any]] = None,
    offer_catalog_key: Optional[str] = None,
    aggregate_rating: Optional[Dict[str, Any]] = None,
    topical_entity: Optional[str] = None,
    save: bool = False,
    csv_path: str = "extracciones.csv",
    jsonl_path: str = "schemas.jsonl",
    as_script: bool = False,
    schema_only: bool = False,
    validate: bool = False,
) -> Dict[str, Any] | str | SchemaValidationResult:
    """
    Genera un schema JSON-LD con opciones de formato y persistencia.

    Args:
        url: URL de la página a procesar.
        nombre: Nombre legible del producto/servicio.
        schema_type: Tipo de schema a generar.
        price_spec: Especificaciones de precio opcionales.
        bank_defaults: Configuración para BankAccount.
        payment_service_defaults: Configuración para PaymentService.
        insurance_defaults: Configuración para InsuranceAgency.
        loan_defaults: Configuración para LoanOrCredit.
        financial_product_defaults: Configuración para FinancialProduct.
        investment_defaults: Configuración para InvestmentOrDeposit.
        blog_defaults: Configuración para BlogPosting.
        event_defaults: Configuración para Event. Requiere start_date (ISO 8601).
        offer_catalog_key: Clave del catálogo de ofertas a incluir.
        aggregate_rating: Rating agregado personalizado.
        topical_entity: Clave de TOPICAL_ENTITY_CHOICES para reemplazar la
            entidad `about` por defecto del tipo (ej. "tarjeta_debito").
        save: Si True, guarda los resultados en archivos.
        csv_path: Ruta del archivo CSV de salida.
        jsonl_path: Ruta del archivo JSONL de salida.
        as_script: Si True, retorna el schema como tag script HTML.
        schema_only: Si True, retorna solo el schema sin metadatos.
        validate: Si True, valida el schema y retorna el resultado.

    Returns:
        Dependiendo de los parámetros:
        - Si validate=True: SchemaValidationResult
        - Si as_script=True: String con tag script HTML
        - Si schema_only=True: Dict con el schema JSON-LD
        - Por defecto: Dict con todos los datos del record
    """
    record = build_schema_from_url(
        url,
        nombre,
        schema_type=schema_type,
        price_spec=price_spec,
        bank_defaults=bank_defaults,
        payment_service_defaults=payment_service_defaults,
        insurance_defaults=insurance_defaults,
        loan_defaults=loan_defaults,
        financial_product_defaults=financial_product_defaults,
        investment_defaults=investment_defaults,
        blog_defaults=blog_defaults,
        event_defaults=event_defaults,
        offer_catalog_key=offer_catalog_key,
        aggregate_rating=aggregate_rating,
        topical_entity=topical_entity,
        validate=validate,
    )

    if save:
        save_outputs(record, csv_path=csv_path, jsonl_path=jsonl_path)

    # Si se pide solo validación, retornar el resultado
    if validate:
        return validate_schema(record.schema)

    if as_script:
        return as_script_tag(record.schema)
    if schema_only:
        return record.schema
    return record.to_dict()
