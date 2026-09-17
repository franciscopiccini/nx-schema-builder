"""CLI mínima para generar schemas desde la terminal."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict

from .config import TOPICAL_ENTITY_CHOICES
from .service.workflow import generate_schema


def _parse_key_value_pairs(values: list[str]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for item in values:
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"El parámetro '{item}' debe tener formato clave=valor")
        key, value = item.split("=", 1)
        result[key] = value
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generador de schema.org para Naranja X.")
    parser.add_argument("url", help="URL a inspeccionar")
    parser.add_argument("nombre", help="Nombre legible del recurso")
    parser.add_argument(
        "--schema-type",
        default="payment_card",
        help="Tipo de schema a generar (payment_card, loan_or_credit, etc.)",
    )
    parser.add_argument(
        "--offer-catalog",
        dest="offer_catalog_key",
        help="Clave del catálogo de offers a adjuntar",
    )
    parser.add_argument(
        "--topical-entity",
        dest="topical_entity",
        choices=sorted(TOPICAL_ENTITY_CHOICES),
        help=(
            "Entidad temática (about) precisa, para cuando el default del tipo "
            "es más genérico que la página (ej. una landing de débito)"
        ),
    )
    parser.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="clave=valor",
        help="Override simple (se acumula y se serializa como cadenas).",
    )
    parser.add_argument(
        "--start-date",
        dest="start_date",
        help="Fecha de inicio del evento en ISO 8601. Obligatorio con --schema-type event.",
    )
    parser.add_argument(
        "--end-date",
        dest="end_date",
        help="Fecha de fin del evento en ISO 8601 (opcional, solo para event).",
    )
    parser.add_argument(
        "--script",
        action="store_true",
        help="Devuelve la salida lista para embeber en HTML.",
    )
    parser.add_argument(
        "--schema-only",
        action="store_true",
        help="Devuelve únicamente el grafo schema.org, sin metadatos auxiliares.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        overrides = _parse_key_value_pairs(args.overrides)
    except argparse.ArgumentTypeError as exc:
        parser.error(str(exc))
        return 2

    kwargs: Dict[str, Any] = {"as_script": args.script, "schema_only": args.schema_only}
    kwargs.update(overrides)
    if args.offer_catalog_key:
        kwargs["offer_catalog_key"] = args.offer_catalog_key
    if args.topical_entity:
        kwargs["topical_entity"] = args.topical_entity

    # build_event_graph espera un dict anidado, que --set no puede expresar
    # (solo acumula pares clave=valor planos). Por eso las fechas entran por
    # flags propios y se arman acá como event_defaults.
    event_defaults: Dict[str, Any] = {}
    if args.start_date:
        event_defaults["start_date"] = args.start_date
    if args.end_date:
        event_defaults["end_date"] = args.end_date
    if event_defaults:
        kwargs["event_defaults"] = event_defaults

    result = generate_schema(
        args.url,
        args.nombre,
        schema_type=args.schema_type,
        **kwargs,
    )

    if args.script:
        sys.stdout.write(result)
    else:
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2))
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
