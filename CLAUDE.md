# fintech-schema-builder

Genera JSON-LD de Schema.org para las landings de Naranja X. Descarga una URL, extrae metadata (título, descripción, imagen, FAQs, texto) y arma un `@graph` según el tipo de producto. Se usa por CLI, API Python, Streamlit o servidor MCP. Docs y comentarios en español.

## Qué archivo usar

| Tarea | Archivo |
|---|---|
| Generar el schema de una landing | `python -m schema_automation.cli` (ver [Comandos](#comandos)) |
| Saber qué regla de modelado respetar al tocar un builder | [docs/reglas-jsonld.md](docs/reglas-jsonld.md) |
| Ver qué propiedades faltan y en qué orden atacarlas | [docs/analisis/2026-06_auditoria-schemas.md](docs/analisis/2026-06_auditoria-schemas.md) |
| Ver un JSON-LD completo de referencia para PaymentCard | [docs/analisis/2026-06_caso-payment-card-tarjeta-naranja.md](docs/analisis/2026-06_caso-payment-card-tarjeta-naranja.md) |
| Cambiar organizaciones, tasas, montos o catálogos | [src/schema_automation/config.py](src/schema_automation/config.py) |
| Agregar un tipo de schema | Nuevo `build_*_graph(ctx, **kwargs)` en `schema/`, registrado en `SCHEMA_BUILDERS` de [schema/\_\_init\_\_.py](src/schema_automation/schema/__init__.py) |
| Agregar un catálogo de ofertas | `OFFER_CATALOGS` en [config.py](src/schema_automation/config.py) |
| Usar el generador desde otra carpeta | [mcp_server.py](mcp_server.py) |
| Cambiar la validación | [validation/validator.py](src/schema_automation/validation/validator.py) |

## Comandos

```bash
pip install -e .            # producción
pip install -e .[dev]       # + pytest y requests-mock
pip install -e .[mcp]       # + SDK de MCP (>=2.0), solo para mcp_server.py

python -m schema_automation.cli URL "Nombre" --schema-type payment_card --schema-only
python -m schema_automation.cli URL "Nombre" --schema-type payment_card --script
python -m schema_automation.cli URL "Nombre" --schema-type event --start-date 2026-11-30T00:00:00-03:00
python -m schema_automation.cli --help

streamlit run streamlit_app.py

claude mcp add schemas --scope local -- <repo>/.venv/bin/python <repo>/mcp_server.py
```

Flags del CLI: `--schema-type`, `--offer-catalog`, `--topical-entity {tarjeta_credito,tarjeta_debito}`, `--set clave=valor`, `--start-date`, `--end-date`, `--script`, `--schema-only`.

API Python: `generate_schema(url, nombre, schema_type=..., schema_only=..., as_script=..., save=...)` en [service/workflow.py](src/schema_automation/service/workflow.py).

Streamlit Cloud: la app apunta a `streamlit_app.py` en la raíz. Instala las dependencias de `pyproject.toml`.

## Tipos

- **`--schema-type`:** `payment_card`, `loan_or_credit`, `bank_account`, `payment_service`, `investment_or_deposit`, `insurance_agency`, `financial_product`, `blog_posting`, `event`.
- **`--offer-catalog`:** `prestamos`, `tarjeta_credito`, `seguros`, `comercios`, `cuenta`.

## Flujo

CLI / Streamlit / MCP → `service/workflow.py` → `infrastructure/http.py` (fetch) → `extraction/` (metadata) → builder de `schema/` → `validation/` → salida (JSON, `<script>` o archivos).

## Árbol

```
CLAUDE.md                     índice (este archivo)
pyproject.toml                dependencias y extras dev / mcp
requirements.txt              dependencias para entornos sin pip install -e
streamlit_app.py              entrada de Streamlit Cloud; agrega src/ al path
mcp_server.py                 servidor MCP por stdio: generar_schema_desde_url, generar_schema_sin_fetch, validar_jsonld, listar_tipos_de_schema
.github/workflows/ci.yml      pytest en Python 3.11; acepta suite vacía (exit 5)
.devcontainer/                configuración de dev container
docs/
  reglas-jsonld.md            reglas de modelado que aplica el código
  analisis/
    2026-06_auditoria-schemas.md              propiedades faltantes por builder y prioridades
    2026-06_caso-payment-card-tarjeta-naranja.md  JSON-LD propuesto para Tarjeta Naranja X
src/schema_automation/
  cli.py                      CLI
  config.py                   defaults: organizaciones, logo, tasas, catálogos, entidades temáticas
  models.py                   SchemaContext (entrada), ExtractionResult, SchemaRecord (salida)
  service/workflow.py         orquestación: build_schema_from_url(), generate_schema()
  extraction/html.py          parseo del HTML
  extraction/meta.py          og: tags y meta
  extraction/faqs.py          FAQs: acordeón de Naranja X, con fallback genérico
  extraction/text.py          texto del body
  schema/base.py              helpers compartidos: deep_merge, build_offer_node, build_webpage_node, build_product_node
  schema/<tipo>.py            un builder por tipo; catalog.py arma el OfferCatalog
  validation/validator.py     validador de estructura JSON-LD
  infrastructure/http.py      cliente HTTP: 3 reintentos, cache SQLite de 15 min, errores FetchError y subclases
  infrastructure/persistence.py  CSV/JSONL y tag <script>
  interfaces/streamlit_app.py UI de Streamlit
```

No hay tests. La CI corre `pytest` y acepta la suite vacía.

## Datos que produce

`generate_schema(..., save=True)` acumula resultados en dos archivos:

- **`extracciones.csv`:** `url`, `name`, `title`, `description`, `image`, `faqs_count`, `faqs_json`.
- **`schemas.jsonl`:** una línea por URL con `url` y `schema`.

Cache HTTP: `schema_automation_cache.sqlite` en la raíz (ignorado por git).
