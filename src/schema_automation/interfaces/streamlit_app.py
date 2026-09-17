"""Interfaz de Streamlit para generar schemas JSON-LD."""

from __future__ import annotations

import json
from typing import Dict, List, Tuple

import streamlit as st

from ..service.workflow import generate_schema

SCHEMA_OPTIONS: List[Tuple[str, str]] = [
    ("PaymentCard", "payment_card"),
    ("LoanOrCredit", "loan_or_credit"),
    ("BankAccount", "bank_account"),
    ("BlogPosting", "blog_posting"),
    ("PaymentService", "payment_service"),
    ("InvestmentOrDeposit", "investment_or_deposit"),
    ("InsuranceAgency", "insurance_agency"),
    ("FinancialProduct", "financial_product"),
    ("Event", "event"),
]

OFFER_CATALOG_OPTIONS: List[Tuple[str, str]] = [
    ("Seleccionar...", ""),
    ("Préstamos", "prestamos"),
    ("Tarjeta de crédito", "tarjeta_credito"),
    ("Seguros", "seguros"),
    ("Cuenta", "cuenta"),
    ("Comercios", "comercios"),
]

DEFAULT_GENERATE_KWARGS: Dict[str, object] = {
    "investment_defaults": {
        "globals": {
            "duration": "P28D",
            "interest_rate": "42",
        }
    }
}

SCHEMA_LABEL_TO_KEY = {label: key for label, key in SCHEMA_OPTIONS}
OFFER_LABEL_TO_KEY = {label: key for label, key in OFFER_CATALOG_OPTIONS}


def _schema_default_index(default_key: str) -> int:
    for idx, (_, key) in enumerate(SCHEMA_OPTIONS):
        if key == default_key:
            return idx
    return 0


def main() -> None:
    """Punto de entrada principal para Streamlit."""
    st.set_page_config(page_title="Schema Automation", page_icon="🧩", layout="centered")

    st.title("Schema Automation")
    st.write(
        "Genera grafos schema.org a partir de una URL pública sin necesidad de notebooks."
    )

    include_offer = st.checkbox("Incluir OfferCatalog", key="include_offer_toggle")
    offer_label = st.selectbox(
        "Catálogo",
        options=[label for label, _ in OFFER_CATALOG_OPTIONS],
        disabled=not include_offer,
        key="offer_label_select",
    )

    with st.form("schema_form"):
        url = st.text_input("URL", placeholder="https://www.naranjax.com")
        nombre = st.text_input("Nombre legible", placeholder="Nombre del producto o servicio")
        schema_label = st.selectbox(
            "Tipo de schema",
            options=[label for label, _ in SCHEMA_OPTIONS],
            index=_schema_default_index("payment_card"),
        )
        output_mode = st.radio(
            "Formato de salida",
            options=("JSON", "Script HTML"),
            index=0,
            horizontal=True,
        )
        submitted = st.form_submit_button("Generar schema")

    if not submitted:
        return

    url = url.strip()
    nombre = nombre.strip()

    if not url or not nombre:
        st.error("La URL y el nombre son obligatorios para generar el schema.")
        return

    kwargs = DEFAULT_GENERATE_KWARGS.copy()
    offer_key = OFFER_LABEL_TO_KEY.get(offer_label, "")
    if include_offer and offer_key:
        kwargs["offer_catalog_key"] = offer_key

    as_script = output_mode == "Script HTML"
    if not as_script:
        kwargs["schema_only"] = True

    try:
        result = generate_schema(
            url,
            nombre,
            schema_type=SCHEMA_LABEL_TO_KEY[schema_label],
            as_script=as_script,
            **kwargs,
        )
    except Exception as exc:  # pragma: no cover - orientado a retro alimentacion visual
        st.error(f"No se pudo generar el schema: {exc}")
        return

    if as_script:
        st.subheader("Script listo para embeber en HTML")
        st.code(result, language="html")
        st.download_button(
            "Descargar script",
            result,
            file_name="schema.html",
            mime="text/html",
        )
        return

    st.subheader("Schema JSON-LD")
    json_payload = json.dumps(result, ensure_ascii=False, indent=2)
    st.code(json_payload, language="json")
    st.download_button(
        "Descargar JSON",
        json_payload,
        file_name="schema.json",
        mime="application/json",
    )


if __name__ == "__main__":  # pragma: no cover - requerido para ejecución directa con python
    main()
