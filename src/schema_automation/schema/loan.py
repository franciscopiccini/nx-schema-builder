"""Builder para schemas de LoanOrCredit."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from ..config import LOAN_OR_CREDIT_DEFAULTS, default_price_valid_until
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


def build_loan_or_credit_graph(
    ctx: SchemaContext,
    price_spec: Optional[Dict[str, Any]] = None,
    loan_defaults: Optional[Dict[str, Any]] = None,
    **_,
) -> List[Dict[str, Any]]:
    """Construye el grafo JSON-LD para un préstamo o crédito."""
    graph: List[Dict[str, Any]] = []
    added_orgs: set = set()

    defaults = deep_merge(LOAN_OR_CREDIT_DEFAULTS, loan_defaults or {})
    amount_cfg = defaults.get("amount", {})
    currency_value = defaults.get("currency") or amount_cfg.get("currency")
    loan_term_cfg = defaults.get("loan_term", {})
    interest_rate_cfg = defaults.get("interest_rate", {})
    apr_cfg = defaults.get("annual_percentage_rate", {})
    repayment_cfg = defaults.get("loan_repayment_form", {})
    loan_type_value = defaults.get("loan_type") or ctx.name

    def _quantitative_node(cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(cfg, dict):
            return None
        node: Dict[str, Any] = {"@type": cfg.get("@type", "QuantitativeValue")}
        has_value = False
        for key in ("minValue", "maxValue", "unitText", "value"):
            value = cfg.get(key)
            if value is not None:
                node[key] = value
                if key != "unitText":
                    has_value = True
        return node if has_value or len(node) > 1 else None

    offer_id = f"{ctx.page_url}#Offer"

    loan_node: Dict[str, Any] = {
        "@type": "LoanOrCredit",
        "@id": f"{ctx.page_url}#LoanOrCredit",
        "url": ctx.page_url,
        "name": ctx.name,
        "provider": [
            organization_reference("naranja_digital"),
            organization_reference("tarjeta_naranja"),
        ],
        "mainEntityOfPage": {"@type": "WebPage", "@id": f"{ctx.page_url}#WebPage"},
        "offers": {"@id": offer_id},
        "loanType": loan_type_value,
    }

    if currency_value:
        loan_node["currency"] = currency_value

    if isinstance(amount_cfg, dict) and amount_cfg:
        amount_node: Dict[str, Any] = {"@type": "MonetaryAmount"}
        amount_currency = amount_cfg.get("currency", currency_value)
        if amount_currency:
            amount_node["currency"] = amount_currency
        for key in ("minValue", "maxValue"):
            value = amount_cfg.get(key)
            if value is not None:
                amount_node[key] = value
        if len(amount_node) > 1:
            loan_node["amount"] = amount_node

    term_node = _quantitative_node(loan_term_cfg)
    if term_node:
        loan_node["loanTerm"] = term_node

    interest_node = _quantitative_node(interest_rate_cfg)
    if interest_node:
        loan_node["interestRate"] = interest_node

    apr_node = _quantitative_node(apr_cfg)
    if apr_node:
        loan_node["annualPercentageRate"] = apr_node

    if isinstance(repayment_cfg, dict) and repayment_cfg:
        repayment_node: Dict[str, Any] = {"@type": repayment_cfg.get("@type", "RepaymentSpecification")}
        for key in ("name", "description"):
            value = repayment_cfg.get(key)
            if value:
                repayment_node[key] = value
        if len(repayment_node) > 1:
            loan_node["loanRepaymentForm"] = repayment_node

    if ctx.image_url:
        loan_node["image"] = {"@type": "ImageObject", "@id": f"{ctx.page_url}#LoanImage", "url": ctx.image_url}
    graph.append(loan_node)

    offer_price = "0"
    if price_spec and isinstance(price_spec, dict):
        price_candidate = price_spec.get("price")
        if price_candidate not in (None, ""):
            offer_price = str(price_candidate)
    price_valid_until = default_price_valid_until()

    offer = build_offer_node(
        ctx.page_url,
        offer_id,
        {
            "name": ctx.name,
            "priceCurrency": "ARS",
            "areaServed": "AR",
            "availability": "https://schema.org/InStock",
            "validFrom": date.today().isoformat(),
            "priceValidUntil": price_valid_until,
            "price": offer_price,
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

    append_organization(graph, resolve_organization({}, "naranja_digital"), added_orgs)
    append_organization(graph, resolve_organization({}, "tarjeta_naranja"), added_orgs)
    append_brand_organization(graph, added_orgs)

    return graph
