# Reglas del JSON-LD

Reglas que el código ya aplica. Cada cambio a un builder tiene que respetarlas. Los demás documentos las referencian y no las repiten.

## Identificadores (`@id`)

- Los nodos de la página usan `{page_url}#Sufijo`. Los sufijos actuales son mixtos (`#PaymentCard`, `#bankaccount`, `#producto`, `#insurance-agency`) y se dejan así. Schema.org no define convención de nombres para `@id`.
- No renombrar un sufijo existente. Los catálogos de `OFFER_CATALOGS` en `config.py` apuntan a las landings por `id_suffix` (por ejemplo `#bankaccount`), y las landings publicadas ya usan esos `@id`.
- Las organizaciones y el logo tienen `@id` fijos en `config.py`: `#OrgNaranjaX`, `#OrgTarjetaNaranja`, `#OrgNaranjaDigital` y `#Logo`.

## Referencias entre nodos

- Una organización se define completa una sola vez en el `@graph`. Los demás nodos la referencian con `{"@id": ...}`.
- Hay un único nodo `#Logo`. Las emisoras lo referencian por `@id`. La excepción es `#LogoNaranjaXInvestment`, que es otra imagen.
- `sameAs` vive solo en la marca (`#OrgNaranjaX`, lista `ORG_SAME_AS`). Las emisoras se identifican por CUIT y se vinculan a la marca por `parentOrganization`. Los nodos de producto no llevan `sameAs`.
- No se inventan códigos de producto en `identifier`: Naranja X no publica ninguno. `financial_product` e `investment_or_deposit` usan como fallback el slug del nombre. En el benchmark, Amex y Capital One no declaran `identifier` en sus tarjetas.
- `termsOfService` y `potentialAction` (`ApplyAction`) apuntan a la propia landing. El PDF de Términos y Condiciones cambia seguido, y cada landing permite pedir el producto. `feesAndCommissionsSpecification` apunta a `https://www.naranjax.com/costos-comisiones-y-limites`.
- `brand` en `Product` es `{"@type": "Brand", "name": "Naranja X"}` (`PRODUCT_BRAND`). Nunca `Organization`: Google lo marca como tipo inválido.

## Datos que no se inventan

- `aggregateRating` solo se emite si el caller lo pasa, respaldado por reviews reales. No hay default: un rating sin fuente es structured data engañoso y expone el sitio a una acción manual.
- `Event` exige `start_date` (`--start-date` en el CLI). Sin fecha el builder falla en lugar de inventarla.
- No afirmar cuotas ni tasas que la página no ofrece. En `financial_product`, la descripción del `priceSpecification` solo se emite con tasas reales o una descripción explícita.
- Tasas y montos de `loan_or_credit` salen de la letra chica de naranjax.com/prestamos (`LOAN_OR_CREDIT_DEFAULTS` en `config.py`).
- El `about` de la `WebPage` usa una entidad neutral por tipo. Para una entidad más precisa se pasa `topical_entity` (`--topical-entity`). Las entidades están verificadas contra Wikidata.

## Merchant listings (Search Console)

- Todo `Offer` lleva `price`, `availability` y `validFrom`.
- El `Offer` de `payment_card` lleva `price: "0"`: la tarjeta no tiene comisión de emisión. Las tasas de financiación van aparte, en `priceSpecification`.
- `hasMerchantReturnPolicy` y `shippingDetails` quedan afuera a propósito. Son campos de productos físicos.

## Salida

- El tag `<script>` escapa `<`, `>` y `&` como escapes Unicode (`as_script_tag` en `infrastructure/persistence.py`).
- Los defaults viven en `config.py`. Los overrides se combinan con `deep_merge()` sobre una copia profunda.
