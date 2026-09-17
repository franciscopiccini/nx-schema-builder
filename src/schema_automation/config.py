"""Constantes y configuración compartida para la generación de schemas."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

# Fechas y rating por defecto -------------------------------------------------

DEFAULT_PRICE_VALIDITY_DAYS = 365


def default_price_valid_until(days: int = DEFAULT_PRICE_VALIDITY_DAYS) -> str:
    """Devuelve una fecha ISO usada como `priceValidUntil` por defecto."""
    return (date.today() + timedelta(days=days)).isoformat()


# No hay AggregateRating por defecto a propósito. El valor que vivía acá
# (4.5 / 1.070.000) no provenía de reviews reales y se inyectaba en todas las
# páginas. Un rating sin respaldo verificable es motivo de acción manual por
# structured data engañoso. Si alguna vez se emite uno, debe venir de una
# fuente real y pasarse explícito vía el parámetro `aggregate_rating`.

DEFAULT_LANGUAGE = "es-AR"

# Entidades de identidad de la organización (sameAs) --------------------------
# Solo identificadores estables. Wikidata (Q124313742) es el sucesor oficial de
# Freebase; Wikipedia es estable. Se descartan a propósito los Google Knowledge
# Graph IDs (Google los fusiona/purga) y los Freebase /m/ (discontinuados 2016).
# Las tres razones sociales comparten CUIT y resuelven a la misma entidad, así
# que las tres exponen el mismo set de perfiles oficiales.
#
# Perfiles sociales: todas las URLs verificadas contra la plataforma (HTTP 200 y
# titular de la cuenta confirmado). Instagram y el canal de YouTube están además
# declarados en Wikidata (P2003 y P2397), o sea confirmados por fuente externa.
ORG_SAME_AS = [
    # Identificadores de knowledge graph
    "https://www.wikidata.org/wiki/Q124313742",
    "https://es.wikipedia.org/wiki/Naranja_X",
    "https://en.wikipedia.org/wiki/Naranja_X",
    # Perfiles sociales oficiales
    "https://www.instagram.com/naranjax/",
    "https://www.facebook.com/NaranjaX/",
    "https://x.com/naranjax",
    # URL de canal (inmutable) en lugar del handle @NaranjaX, que es renombrable.
    "https://www.youtube.com/channel/UCMaU6V3NWWnXpdNnM6cirpQ",
    "https://ar.linkedin.com/company/naranjax",
    "https://www.tiktok.com/@naranjaxoficial",
]

# Organizaciones y direcciones -------------------------------------------------
# Modelo marca / emisoras. Hay DOS razones sociales reales (Tarjeta Naranja y
# Naranja Digital), cada una con su CUIT propio. "Naranja X" no es una tercera
# sociedad: es la marca comercial que representa a ambas, y es la entidad a la
# que apuntan Wikidata, Wikipedia y los perfiles sociales.
#
# Por eso el sameAs completo vive SOLO en la marca: el Instagram es de Naranja X,
# no de "Tarjeta Naranja S.A.U.". Las emisoras se identifican por su CUIT y se
# vinculan a la marca por parentOrganization, sin heredar los perfiles sociales.

_LOGO_URL = "https://images.ctfassets.net/yxlyq25bynna/1IxKUBv3dtISflaWQoSIZW/11e239808ff23ee64b26ba44bfcd93a0/Logo_NX.jpeg"

# Un unico nodo de logo compartido. Las tres orgs usan el mismo archivo, así que
# darle un @id distinto a cada una declaraba tres ImageObject separados
# afirmando ser la misma imagen. Con un solo @id el grafo dice lo que es: una
# imagen, referenciada desde varias organizaciones.
LOGO_ID = "https://www.naranjax.com/#Logo"

LOGO_NODE: Dict[str, object] = {
    "@type": "ImageObject",
    "@id": LOGO_ID,
    "url": _LOGO_URL,
    "contentUrl": _LOGO_URL,
}

NARANJA_X_ID = "https://www.naranjax.com/#OrgNaranjaX"

ORGANIZATIONS: Dict[str, Dict[str, object]] = {
    # Marca: concentra la identidad de entidad (sameAs) y publica el sitio.
    "naranja_x": {
        "@type": "Organization",
        "@id": NARANJA_X_ID,
        "name": "Naranja X",
        "url": "https://www.naranjax.com/",
        # La marca define el nodo completo; las emisoras lo referencian por @id.
        "logo": dict(LOGO_NODE),
        "sameAs": list(ORG_SAME_AS),
        # Sin subOrganization: cada página emite solo la emisora que interviene
        # en ese producto, así que listar ambas dejaría un @id sin resolver en
        # el grafo. La relación ya la declara parentOrganization desde la
        # emisora, que siempre está presente cuando se la referencia.
    },
    # Emisoras: entidades legales. CUIT propio, sin perfiles sociales.
    "tarjeta_naranja": {
        "@type": "Organization",
        "@id": "https://www.naranjax.com/#OrgTarjetaNaranja",
        "name": "Tarjeta Naranja S.A.U.",
        "url": "https://www.naranjax.com/",
        "logo": {"@id": LOGO_ID},
        "parentOrganization": {"@id": NARANJA_X_ID},
        "brand": {"@id": NARANJA_X_ID},
        "identifier": {
            "@type": "PropertyValue",
            "propertyID": "CUIT",
            "value": "30-68537634-9",
        },
    },
    "naranja_digital": {
        "@type": "Organization",
        "@id": "https://www.naranjax.com/#OrgNaranjaDigital",
        "name": "Naranja Digital Compañía Financiera S.A.U.",
        "url": "https://www.naranjax.com/",
        "logo": {"@id": LOGO_ID},
        "parentOrganization": {"@id": NARANJA_X_ID},
        "brand": {"@id": NARANJA_X_ID},
        "identifier": {
            "@type": "PropertyValue",
            "propertyID": "CUIT",
            "value": "30-71663964-5",
        },
    },
}

NARANJA_X_ADDRESSES: List[Dict[str, object]] = [
    {
        "@type": "PostalAddress",
        "name": "Casa Naranja",
        "streetAddress": "La Tablada 451",
        "addressLocality": "Córdoba",
        "addressRegion": "Córdoba",
        "postalCode": "X5000",
        "addressCountry": "AR",
    },
    {
        "@type": "PostalAddress",
        "name": "Naranja X Buenos Aires",
        "streetAddress": "Leiva 4070",
        "addressLocality": "Ciudad Autónoma de Buenos Aires",
        "addressRegion": "Buenos Aires",
        "postalCode": "C1427BQA",
        "addressCountry": "AR",
    },
]

WEBPAGE_DEFAULTS = {
    "@type": "WebPage",
    "inLanguage": DEFAULT_LANGUAGE,
    "isPartOf": {
        "@type": "WebSite",
        "@id": "https://www.naranjax.com/#website",
    },
    # El sitio lo publica la marca, no una de las emisoras.
    "publisher": {"@id": ORGANIZATIONS["naranja_x"]["@id"]},
}

# Entidades temáticas por tipo de schema (about de la WebPage) ----------------
# Cada concepto es una entidad de Wikidata verificada (sentido correcto elegido
# a mano) con su artículo de Wikipedia ES cuando existe. Se adjuntan como `about`
# al nodo WebPage para dar a los crawlers contexto semántico sin más contenido en
# página. Solo Wikidata + Wikipedia (identificadores estables).
# Se omiten a propósito:
#   - payment_service: sin entidad de Wikidata con sentido limpio.
#   - blog_posting: el `about` de un artículo es su tema real, no un concepto genérico.
TOPICAL_ENTITIES: Dict[str, Dict[str, str]] = {
    "payment_card": {
        "@id": "https://www.wikidata.org/wiki/Q161380",
        "name": "Tarjeta de crédito",
        "sameAs": "https://es.wikipedia.org/wiki/Tarjeta_de_cr%C3%A9dito",
    },
    "loan_or_credit": {
        "@id": "https://www.wikidata.org/wiki/Q182076",
        "name": "Crédito",
        "sameAs": "https://es.wikipedia.org/wiki/Cr%C3%A9dito",
    },
    "bank_account": {
        "@id": "https://www.wikidata.org/wiki/Q676459",
        "name": "Cuenta bancaria",
        "sameAs": "https://es.wikipedia.org/wiki/Cuenta_bancaria",
    },
    "investment_or_deposit": {
        "@id": "https://www.wikidata.org/wiki/Q4290",
        "name": "Inversión",
        "sameAs": "https://es.wikipedia.org/wiki/Inversi%C3%B3n",
    },
    "insurance_agency": {
        "@id": "https://www.wikidata.org/wiki/Q43183",
        "name": "Seguro",
        "sameAs": "https://es.wikipedia.org/wiki/Seguro",
    },
    "financial_product": {
        # Q15809678 no tiene artículo en Wikipedia ES → sin sameAs.
        "@id": "https://www.wikidata.org/wiki/Q15809678",
        "name": "Producto financiero",
    },
}

# Defaults de productos -------------------------------------------------------

PRICE_SPEC_DEFAULT = {
    "TNA": {"min": 55, "max": 153},
    "TEA": {"min": 71.22, "max": 322.08},
    "CFTEA": {"min": 91.11, "max": 459.39},
}

PAYMENT_SERVICE_DEFAULTS = {
    "area_served": {"@type": "Country", "name": "Argentina"},
    "provider": {
        "org_key": "naranja_x",
    },
    "offer": {
        "price_currency": "ARS",
        "eligible_region": "AR",
    },
}

INSURANCE_AGENCY_DEFAULTS = {
    "agency": {
        "id_suffix": "#insurance-agency",
        "area_served": {"@type": "AdministrativeArea", "name": "Argentina"},
        "addresses": NARANJA_X_ADDRESSES,
        "identifier": {
            "propertyID": "CUIT",
            "value": "30-68537634-9",
        },
        # Sin "id": era un typo por "@id" y schema.org no define la propiedad
        # `id`, así que el expandido JSON-LD la descartaba. Además duplicaba
        # `url`; un @id de nodo no es la URL del archivo.
        "logo": {
            "url": "https://images.ctfassets.net/yxlyq25bynna/1IxKUBv3dtISflaWQoSIZW/11e239808ff23ee64b26ba44bfcd93a0/Logo_NX.jpeg",
            "contentUrl": "https://images.ctfassets.net/yxlyq25bynna/1IxKUBv3dtISflaWQoSIZW/11e239808ff23ee64b26ba44bfcd93a0/Logo_NX.jpeg",
        },
        "same_as": [],
    },
    "product": {
        "id_suffix": "#producto",
        "category": "Insurance",
    },
    "offer": {
        "id_suffix": "#offer-basica",
        "name": "Cobertura Básica",
        "price_currency": "ARS",
        "availability": "https://schema.org/InStock",
        "area_served": "AR",
        "eligible_region": "AR",
    },
}

FINANCIAL_PRODUCT_ZERO_RATES = {
    "TNA": 0,
    "TEA": 0,
    "CFT": 0,
}

LOAN_OR_CREDIT_DEFAULTS = {
    "amount": {
        "currency": "ARS",
        "minValue": 10000,
        "maxValue": 20000000,
    },
    "currency": "ARS",
    "loan_term": {
        "@type": "QuantitativeValue",
        "maxValue": 48,
        "unitText": "MONTH",
    },
    "interest_rate": {
        "minValue": 45.0,
        "maxValue": 149.0,
        "unitText": "PERCENT",
    },
    "annual_percentage_rate": {
        "minValue": 70.32,
        "maxValue": 436.38,
        "unitText": "PERCENT",
    },
    "loan_repayment_form": {
        "@type": "RepaymentSpecification",
        "name": "Sistema de amortización francés",
        "description": "Cuotas fijas mensuales con interés fijo durante todo el plazo (método francés).",
    },
}

FINANCIAL_PRODUCT_DEFAULTS = {
    "area_served": "AR",
    "provider": {
        "org_key": "tarjeta_naranja",
    },
    "offer": {
        "price_currency": "ARS",
        "billing_increment": "1",
        "min_price": "0",
        "area_served": "AR",
        "valid_from_offset": 0,
        "valid_through_offset": 30,
        # Sin plantilla por defecto: afirmar cuotas o tasas sobre un producto
        # financiero genérico es incorrecto (p. ej. compra de dólares, que no
        # tiene financiación). Cada landing con financiación real pasa su
        # propio "rates" o "description".
        "description_template": "",
    },
    "product": {
        "id_suffix": "#financial-product",
    },
    "faq_id_suffix": "#FAQPage",
}

INVESTMENT_OR_DEPOSIT_DEFAULTS = {
    "area_served": "AR",
    "globals": {
        "duration": "",
        "interest_rate": "",
    },
    "provider": {
        "org_key": "naranja_x",
        "overrides": {
            "logo": {
                "@type": "ImageObject",
                "@id": "https://www.naranjax.com/#LogoNaranjaXInvestment",
                "url": "https://images.ctfassets.net/yxlyq25bynna/5aunl52F9uDLxXLUC8L7O4/b025683cc1824c386a19c478a5dd46ae/isologo-naranjax.png",
                "contentUrl": "https://images.ctfassets.net/yxlyq25bynna/5aunl52F9uDLxXLUC8L7O4/b025683cc1824c386a19c478a5dd46ae/isologo-naranjax.png",
            }
        },
    },
    "investment": {
        "id_suffix": "#producto",
        "types": ["InvestmentOrDeposit"],
        "alternate_name": "Ahorro por objetivos con TNA",
        "service_type": "Ahorro por objetivos con interés (TNA)",
        "audience": {
            "@type": "Audience",
            "audienceType": "Usuarios de banca minorista en Argentina",
        },
        "interest_rate": {
            "type": "QuantitativeValue",
            "unit_text": "TNA",
        },
    },
    "offer": {
        "id_suffix": "#offer",
        "price_currency": "ARS",
        "area_served": "AR",
        "eligible_region": "AR",
        "availability": "https://schema.org/InStock",
        "valid_from_offset": 0,
        "valid_through_offset": 28,
    },
    "product": {
        "id_suffix": "#product",
    },
    "faq_id_suffix": "#FAQPage",
}

# Catálogos -------------------------------------------------------------------

OFFER_CATALOGS: Dict[str, Dict[str, object]] = {
    "prestamos": {
        "name": "Catálogo de Préstamos",
        "items": [
            {
                "name": "Préstamos para monotributistas",
                "url": "https://www.naranjax.com/prestamos/monotributistas",
                "id_suffix": "#LoanOrCredit",
            },
            {
                "name": "Préstamos express",
                "url": "https://www.naranjax.com/prestamos/express",
                "id_suffix": "#LoanOrCredit",
            },
            {
                "name": "Préstamos para viajes",
                "url": "https://www.naranjax.com/prestamos/viajes",
                "id_suffix": "#LoanOrCredit",
            },
        ],
    },
    "tarjeta_credito": {
        "name": "Catálogo de Tarjetas de Crédito",
        "items": [
            {
                "name": "Tarjeta Naranja X",
                "url": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja",
                "id_suffix": "#PaymentCard",
            },
            {
                "name": "Tarjeta Naranja X Visa",
                "url": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja-visa",
                "id_suffix": "#PaymentCard",
            },
            {
                "name": "Tarjeta Naranja X Mastercard",
                "url": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja-mastercard",
                "id_suffix": "#PaymentCard",
            },
        ],
    },
    "seguros": {
        "name": "Catálogo de Seguros",
        "items": [
            {
                "name": "Seguro de Vida",
                "url": "https://www.naranjax.com/seguros/vida",
                "id_suffix": "#producto",
            },
            {
                "name": "Seguro para Celulares",
                "url": "https://www.naranjax.com/seguros/celular",
                "id_suffix": "#producto",
            },
            {
                "name": "Seguro para Hogar",
                "url": "https://www.naranjax.com/seguros/hogar",
                "id_suffix": "#producto",
            },
        ],
    },
    "comercios": {
        "name": "Catálogo de Soluciones de Cobro",
        "items": [
            {
                "name": "Cobro Tap",
                "url": "https://www.naranjax.com/cobro-tap-comercios",
                "id_suffix": "#PaymentService",
            },
            {
                "name": "Código QR",
                "url": "https://www.naranjax.com/codigo-qr-comercios",
                "id_suffix": "#PaymentService",
            },
            {
                "name": "Plan Z para negocios",
                "url": "https://www.naranjax.com/planz-negocios",
                "id_suffix": "#PaymentService",
            },
            {
                "name": "Cuenta Negocio",
                "url": "https://www.naranjax.com/cuenta-negocio",
                "id_suffix": "#bankaccount",
            },
        ],
    },
    "cuenta": {
        "name": "Catálogo de Cuentas",
        "items": [
            {
                "name": "Cuenta Remunerada",
                "url": "https://www.naranjax.com/cuenta-remunerada",
                "id_suffix": "#bankaccount",
            },
            {
                "name": "Cuenta en Dólares",
                "url": "https://www.naranjax.com/cuenta-dolar",
                "id_suffix": "#bankaccount",
            },
            {
                "name": "Caja de Ahorro",
                "url": "https://www.naranjax.com/cuentagratuitauniversal",
                "id_suffix": "#bankaccount",
            },
        ],
    },
}
