"""Validador de schemas JSON-LD para schema.org."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

# Tipos válidos de schema.org para productos financieros
VALID_SCHEMA_TYPES: Set[str] = {
    # Tipos principales
    "PaymentCard",
    "LoanOrCredit",
    "BankAccount",
    "PaymentService",
    "FinancialProduct",
    "InvestmentOrDeposit",
    "InsuranceAgency",
    "BlogPosting",
    # Tipos relacionados
    "Organization",
    "Product",
    "Offer",
    "OfferCatalog",
    "WebPage",
    "FAQPage",
    "Question",
    "Answer",
    "ImageObject",
    "AggregateRating",
    "PostalAddress",
    "Place",
    "Country",
    "AdministrativeArea",
    "MonetaryAmount",
    "QuantitativeValue",
    "RepaymentSpecification",
    "UnitPriceSpecification",
    "Person",
    "Audience",
    "PropertyValue",
    "WebSite",
    "Thing",
    # Usados por el builder de Event; ambos existen en el vocabulario oficial.
    "Event",
    "VirtualLocation",
}

# Campos requeridos por tipo de schema
REQUIRED_FIELDS: Dict[str, List[str]] = {
    "PaymentCard": ["@type", "@id", "name"],
    "LoanOrCredit": ["@type", "@id", "name"],
    "BankAccount": ["@type", "@id", "name"],
    "PaymentService": ["@type", "@id", "name"],
    "FinancialProduct": ["@type", "@id", "name"],
    "InvestmentOrDeposit": ["@type", "@id", "name"],
    "InsuranceAgency": ["@type", "@id", "name"],
    "BlogPosting": ["@type", "@id", "headline"],
    "Organization": ["@type", "name"],
    "Product": ["@type", "@id", "name"],
    "Offer": ["@type", "@id"],
    "WebPage": ["@type", "@id"],
    "FAQPage": ["@type", "@id", "mainEntity"],
    "Question": ["@type", "name", "acceptedAnswer"],
    "Answer": ["@type", "text"],
    # startDate es requerido por Google en Event, no solo recomendado.
    "Event": ["@type", "@id", "name", "startDate"],
}

# Entidad HTML que sobrevivió a la extracción (venía doble-escapada en el
# origen). Googlebot aplica un pass de unescaping al leer el JSON-LD, así que
# el texto que indexa no es el que se generó.
HTML_ENTITY_RE = re.compile(
    r"&(?:[a-zA-Z][a-zA-Z0-9]{1,31}|#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6});"
)

# Secuencia que trunca la etiqueta <script type="application/ld+json">.
SCRIPT_CLOSE_RE = re.compile(r"</\s*script", re.IGNORECASE)

# Campos que deben contener URLs válidas
URL_FIELDS: Set[str] = {
    "url",
    "@id",
    "mainEntityOfPage",
    "sameAs",
    "contentUrl",
}


@dataclass
class SchemaValidationError:
    """Representa un error de validación."""

    path: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.path}: {self.message}"


@dataclass
class SchemaValidationResult:
    """Resultado de la validación de un schema."""

    is_valid: bool
    errors: List[SchemaValidationError] = field(default_factory=list)
    warnings: List[SchemaValidationError] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": [{"path": e.path, "message": e.message} for e in self.errors],
            "warnings": [{"path": w.path, "message": w.message} for w in self.warnings],
        }


class SchemaValidator:
    """Validador de schemas JSON-LD."""

    def __init__(self, strict: bool = False):
        """
        Inicializa el validador.

        Args:
            strict: Si True, trata warnings como errores.
        """
        self.strict = strict
        self._errors: List[SchemaValidationError] = []
        self._warnings: List[SchemaValidationError] = []
        self._defined_ids: Set[str] = set()
        self._referenced_ids: Set[str] = set()

    def validate(self, schema: Dict[str, Any]) -> SchemaValidationResult:
        """
        Valida un schema JSON-LD completo.

        Args:
            schema: Schema JSON-LD a validar.

        Returns:
            SchemaValidationResult con errores y warnings.
        """
        self._errors = []
        self._warnings = []
        self._defined_ids = set()
        self._referenced_ids = set()

        # Validar estructura básica
        self._validate_structure(schema)

        # Validar cada nodo del grafo
        if "@graph" in schema:
            for idx, node in enumerate(schema["@graph"]):
                self._validate_node(node, f"@graph[{idx}]")
        elif "@type" in schema:
            self._validate_node(schema, "root")

        # Validar referencias @id
        self._validate_id_references()

        # Detectar contenido que Googlebot reinterpretaría al leer el JSON-LD
        self._validate_escaping(schema, "")

        is_valid = len(self._errors) == 0
        if self.strict:
            is_valid = is_valid and len(self._warnings) == 0

        return SchemaValidationResult(
            is_valid=is_valid,
            errors=self._errors.copy(),
            warnings=self._warnings.copy(),
        )

    def _add_error(self, path: str, message: str) -> None:
        """Agrega un error de validación."""
        self._errors.append(SchemaValidationError(path, message, "error"))

    def _add_warning(self, path: str, message: str) -> None:
        """Agrega un warning de validación."""
        self._warnings.append(SchemaValidationError(path, message, "warning"))

    def _validate_structure(self, schema: Dict[str, Any]) -> None:
        """Valida la estructura básica del schema."""
        if not isinstance(schema, dict):
            self._add_error("root", "El schema debe ser un objeto JSON")
            return

        # Validar @context
        context = schema.get("@context")
        if not context:
            self._add_error("@context", "Falta el campo @context")
        elif context != "https://schema.org":
            self._add_warning("@context", f"Context inesperado: {context}")

        # Debe tener @graph o @type
        if "@graph" not in schema and "@type" not in schema:
            self._add_error("root", "El schema debe tener @graph o @type")

        # Validar que @graph sea una lista
        if "@graph" in schema and not isinstance(schema["@graph"], list):
            self._add_error("@graph", "@graph debe ser una lista")

    def _validate_node(self, node: Any, path: str) -> None:
        """Valida un nodo individual del schema."""
        if not isinstance(node, dict):
            self._add_error(path, "El nodo debe ser un objeto")
            return

        # Validar @type
        node_type = node.get("@type")
        if not node_type:
            self._add_warning(path, "Falta @type en el nodo")
        else:
            self._validate_type(node_type, path)

        # Registrar @id si existe
        node_id = node.get("@id")
        if node_id:
            if node_id in self._defined_ids:
                self._add_warning(f"{path}.@id", f"ID duplicado: {node_id}")
            self._defined_ids.add(node_id)
            self._validate_id_format(node_id, f"{path}.@id")

        # Validar campos requeridos según el tipo
        self._validate_required_fields(node, node_type, path)

        # Validar URLs
        self._validate_urls(node, path)

        # Validar nodos anidados
        self._validate_nested_nodes(node, path)

    def _validate_type(self, node_type: Any, path: str) -> None:
        """Valida el @type de un nodo."""
        types = [node_type] if isinstance(node_type, str) else node_type

        for t in types:
            if t not in VALID_SCHEMA_TYPES:
                self._add_warning(f"{path}.@type", f"Tipo no reconocido: {t}")

    def _validate_required_fields(
        self, node: Dict[str, Any], node_type: Any, path: str
    ) -> None:
        """Valida campos requeridos según el tipo."""
        if not node_type:
            return

        types = [node_type] if isinstance(node_type, str) else node_type
        primary_type = types[0] if types else None

        if primary_type and primary_type in REQUIRED_FIELDS:
            for field_name in REQUIRED_FIELDS[primary_type]:
                if field_name not in node:
                    self._add_error(
                        f"{path}.{field_name}",
                        f"Campo requerido faltante para {primary_type}",
                    )

    def _validate_urls(self, node: Dict[str, Any], path: str) -> None:
        """Valida que los campos URL tengan formato válido."""
        for key, value in node.items():
            if key in URL_FIELDS and isinstance(value, str):
                if not self._is_valid_url_or_id(value):
                    self._add_warning(f"{path}.{key}", f"URL/ID inválido: {value}")

            # Revisar referencias @id en objetos anidados
            if isinstance(value, dict) and "@id" in value:
                ref_id = value["@id"]
                self._referenced_ids.add(ref_id)

            # Revisar listas de referencias
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and "@id" in item:
                        self._referenced_ids.add(item["@id"])

    @staticmethod
    def _is_reference(value: Dict[str, Any]) -> bool:
        """Indica si el objeto es una referencia a otro nodo y no una definición.

        En JSON-LD ``{"@id": "...#OrgNaranjaX"}`` apunta a un nodo definido en
        otra parte del grafo; los campos reales viven allí. Puede traer ``@type``
        como pista sin dejar de ser una referencia. Validarle los campos
        requeridos daría un falso error por cada `publisher`, `author` o `brand`
        expresado por @id, que es justamente la forma recomendada.
        """
        return "@id" in value and not (set(value) - {"@id", "@type"})

    def _validate_nested_nodes(self, node: Dict[str, Any], path: str) -> None:
        """Valida nodos anidados recursivamente."""
        for key, value in node.items():
            if key.startswith("@"):
                continue

            if isinstance(value, dict) and "@type" in value:
                if not self._is_reference(value):
                    self._validate_node(value, f"{path}.{key}")
            elif isinstance(value, list):
                for idx, item in enumerate(value):
                    if isinstance(item, dict) and "@type" in item:
                        if not self._is_reference(item):
                            self._validate_node(item, f"{path}.{key}[{idx}]")

    def _validate_escaping(self, value: Any, path: str) -> None:
        """Recorre los valores string buscando contenido que Google reinterpreta.

        Googlebot aplica un único pass de HTML unescaping sobre el contenido del
        ``<script type="application/ld+json">``. Un ``</script`` crudo trunca la
        etiqueta y una entidad HTML residual se desenrolla un nivel más, así que
        ambos casos se reportan aunque el JSON sea sintácticamente válido.
        """
        if isinstance(value, str):
            if SCRIPT_CLOSE_RE.search(value):
                self._add_warning(
                    path,
                    "Contiene '</script': trunca la etiqueta si no se escapa como \\u003C",
                )
            entity = HTML_ENTITY_RE.search(value)
            if entity:
                self._add_warning(
                    path,
                    f"Entidad HTML sin decodificar ({entity.group()}): "
                    "Googlebot la desescapa un nivel más al leer el JSON-LD",
                )
        elif isinstance(value, dict):
            for key, nested in value.items():
                self._validate_escaping(nested, f"{path}.{key}" if path else key)
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                self._validate_escaping(item, f"{path}[{idx}]")

    def _validate_id_references(self) -> None:
        """Valida que todas las referencias @id apunten a nodos definidos."""
        undefined = self._referenced_ids - self._defined_ids

        # Filtrar referencias a URLs externas (que no son fragmentos locales)
        for ref_id in undefined:
            # Es válido referenciar URLs externas
            if ref_id.startswith("http") and "#" not in ref_id:
                continue
            # Referencias con fragmento deben estar definidas
            if "#" in ref_id:
                self._add_warning(
                    "@id_references",
                    f"Referencia a ID no definido en el grafo: {ref_id}",
                )

    def _validate_id_format(self, node_id: str, path: str) -> None:
        """Valida el formato de un @id."""
        # Los @id deben ser URIs válidas o fragmentos
        if not node_id:
            self._add_error(path, "@id no puede estar vacío")
            return

        if not self._is_valid_url_or_id(node_id):
            self._add_warning(path, f"Formato de @id no estándar: {node_id}")

    def _is_valid_url_or_id(self, value: str) -> bool:
        """Verifica si un valor es una URL o ID válido."""
        if not value:
            return False

        # URLs absolutas
        if value.startswith(("http://", "https://")):
            try:
                result = urlparse(value)
                return bool(result.netloc)
            except Exception:
                return False

        # IDs relativos con fragmento
        if value.startswith("#"):
            return len(value) > 1

        # Referencias schema.org
        if value.startswith("https://schema.org/"):
            return True

        return False


def validate_schema(schema: Dict[str, Any], strict: bool = False) -> SchemaValidationResult:
    """
    Función de conveniencia para validar un schema.

    Args:
        schema: Schema JSON-LD a validar.
        strict: Si True, trata warnings como errores.

    Returns:
        SchemaValidationResult con errores y warnings.
    """
    validator = SchemaValidator(strict=strict)
    return validator.validate(schema)
