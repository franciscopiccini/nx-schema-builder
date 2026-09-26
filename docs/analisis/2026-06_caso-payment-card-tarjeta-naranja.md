# Caso de prueba — PaymentCard "Tarjeta Naranja X"

**URL base:** https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja
**Fecha de tasas:** vigentes del 28/05/2026 al 27/06/2026. Están vencidas: antes de reusar el JSON-LD, tomar las tasas vigentes de la letra chica.
**Validador objetivo:** [validator.schema.org](https://validator.schema.org/)

JSON-LD propuesto que aplica los faltantes de la [auditoría](2026-06_auditoria-schemas.md) a una landing real. No es output del builder.

---

## Tasas reales tomadas como input

| Tasa | Valor |
|---|---|
| TNA (Tasa Nominal Anual) | 84,81 % |
| TEA (Tasa Efectiva Anual) | 126,94 % |
| CFT TNA (con IVA) | 102,6201 % |
| CFT TEA (con IVA) | 167,70 % |
| Cuotas disponibles | 1, 2, 3, 6 y 9 |
| Plan Z (3 cuotas sin interés) | TNA / TEA / CFT = 0,00 % |
| Vigencia | 28/05/2026 → 27/06/2026 |

---

## Estructura del caso

El JSON-LD propuesto incluye **dos `Offer` enlazadas al mismo `PaymentCard`** vía `offers: [...]`:

1. **`#OfferFinanciacionCuotas`** — financiación 2/3/6/9 cuotas (TNA 84,81 %)
2. **`#OfferPlanZ`** — Plan Z 3 cuotas sin interés (TNA 0 %)

Además incluye estos faltantes de la auditoría:

- `brand` en el PaymentCard
- `interestRate` y `annualPercentageRate` como `QuantitativeValue` con `unitText: PERCENT`
- `feesAndCommissionsSpecification` apuntando a /costos-comisiones-y-limites
- `termsOfService` apuntando a la misma landing, que enlaza los Términos y Condiciones vigentes
- `potentialAction` con `ApplyAction` hacia la misma landing, que es donde se pide la tarjeta
- `category: "FinancialProduct/PaymentCard"`
- `itemCondition: NewCondition` en cada Offer
- `eligibleCustomerType` segmentado
- `audience` con `PeopleAudience`
- `priceSpecification` con `UnitPriceSpecification` por cada tasa
- WebPage con `inLanguage: es-AR` y `speakable`
- `price: "0"` en cada Offer (ver [reglas-jsonld.md](../reglas-jsonld.md#merchant-listings-search-console))

---

## JSON-LD propuesto (para pegar en validator.schema.org)

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "PaymentCard",
      "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#PaymentCard",
      "url": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja",
      "name": "Tarjeta Naranja X",
      "description": "Tarjeta de crédito con financiación en 2, 3, 6 y 9 cuotas y promociones Plan Z de 3 cuotas sin interés.",
      "category": "FinancialProduct/PaymentCard",
      "areaServed": {
        "@type": "Country",
        "name": "Argentina"
      },
      "provider": {
        "@id": "https://www.naranjax.com/#OrgTarjetaNaranja"
      },
      "brand": {
        "@type": "Brand",
        "name": "Naranja X",
        "logo": "https://images.ctfassets.net/yxlyq25bynna/1IxKUBv3dtISflaWQoSIZW/11e239808ff23ee64b26ba44bfcd93a0/Logo_NX.jpeg"
      },
      "audience": {
        "@type": "PeopleAudience",
        "audienceType": "Personas mayores de 18 años residentes en Argentina"
      },
      "interestRate": {
        "@type": "QuantitativeValue",
        "value": 84.81,
        "unitText": "PERCENT",
        "name": "TNA — Tasa Nominal Anual"
      },
      "annualPercentageRate": {
        "@type": "QuantitativeValue",
        "value": 102.6201,
        "unitText": "PERCENT",
        "name": "CFT TNA con IVA"
      },
      "feesAndCommissionsSpecification": "https://www.naranjax.com/costos-comisiones-y-limites",
      "termsOfService": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja",
      "mainEntityOfPage": {
        "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#WebPage"
      },
      "image": {
        "@type": "ImageObject",
        "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#PaymentCardImage",
        "url": "https://images.ctfassets.net/yxlyq25bynna/5joZPoK23aJEKyz279Z4DP/894cefa974902d2e61e05eda3ec66b9b/TNaranjaHero.png"
      },
      "potentialAction": {
        "@type": "ApplyAction",
        "name": "Solicitar Tarjeta Naranja X",
        "target": {
          "@type": "EntryPoint",
          "urlTemplate": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja",
          "actionPlatform": [
            "https://schema.org/DesktopWebPlatform",
            "https://schema.org/MobileWebPlatform",
            "https://schema.org/IOSPlatform",
            "https://schema.org/AndroidPlatform"
          ]
        }
      },
      "offers": [
        {
          "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#OfferFinanciacionCuotas"
        },
        {
          "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#OfferPlanZ"
        }
      ]
    },

    {
      "@type": "Offer",
      "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#OfferFinanciacionCuotas",
      "name": "Financiación en 2, 3, 6 y 9 cuotas con plástico Naranja X / Visa / Mastercard / Amex",
      "description": "TNA 84,81 % — TEA 126,94 % — CFT TNA con IVA 102,6201 % — CFT TEA con IVA 167,70 %. Solo válido para clientes que no registren saldos vencidos impagos.",
      "url": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja",
      "price": "0",
      "priceCurrency": "ARS",
      "areaServed": {
        "@type": "Country",
        "name": "Argentina"
      },
      "eligibleRegion": "AR",
      "eligibleCustomerType": "http://purl.org/goodrelations/v1#Enduser",
      "itemCondition": "https://schema.org/NewCondition",
      "availability": "https://schema.org/InStock",
      "validFrom": "2026-05-28",
      "validThrough": "2026-06-27",
      "priceValidUntil": "2026-06-27",
      "seller": {
        "@id": "https://www.naranjax.com/#OrgTarjetaNaranja"
      },
      "priceSpecification": [
        {
          "@type": "UnitPriceSpecification",
          "name": "Tasa Nominal Anual (TNA)",
          "price": 84.81,
          "priceCurrency": "ARS",
          "valueAddedTaxIncluded": false,
          "referenceQuantity": {
            "@type": "QuantitativeValue",
            "value": 1,
            "unitText": "ANN"
          }
        },
        {
          "@type": "UnitPriceSpecification",
          "name": "Tasa Efectiva Anual (TEA)",
          "price": 126.94,
          "priceCurrency": "ARS",
          "valueAddedTaxIncluded": false,
          "referenceQuantity": {
            "@type": "QuantitativeValue",
            "value": 1,
            "unitText": "ANN"
          }
        },
        {
          "@type": "UnitPriceSpecification",
          "name": "CFT TNA con IVA",
          "price": 102.6201,
          "priceCurrency": "ARS",
          "valueAddedTaxIncluded": true,
          "referenceQuantity": {
            "@type": "QuantitativeValue",
            "value": 1,
            "unitText": "ANN"
          }
        },
        {
          "@type": "UnitPriceSpecification",
          "name": "CFT TEA con IVA",
          "price": 167.70,
          "priceCurrency": "ARS",
          "valueAddedTaxIncluded": true,
          "referenceQuantity": {
            "@type": "QuantitativeValue",
            "value": 1,
            "unitText": "ANN"
          }
        }
      ],
      "eligibleDuration": {
        "@type": "QuantitativeValue",
        "minValue": 2,
        "maxValue": 9,
        "unitText": "MON"
      }
    },

    {
      "@type": "Offer",
      "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#OfferPlanZ",
      "name": "Plan Z — 3 cuotas sin interés",
      "description": "Plan en Zeta 3 cuotas cero interés. CFT 0,00 % — TNA 0,00 % — TEA 0,00 %.",
      "url": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja",
      "price": "0",
      "priceCurrency": "ARS",
      "areaServed": {
        "@type": "Country",
        "name": "Argentina"
      },
      "eligibleRegion": "AR",
      "eligibleCustomerType": "http://purl.org/goodrelations/v1#Enduser",
      "itemCondition": "https://schema.org/NewCondition",
      "availability": "https://schema.org/InStock",
      "validFrom": "2026-05-28",
      "validThrough": "2026-06-27",
      "priceValidUntil": "2026-06-27",
      "seller": {
        "@id": "https://www.naranjax.com/#OrgTarjetaNaranja"
      },
      "priceSpecification": [
        {
          "@type": "UnitPriceSpecification",
          "name": "Tasa Nominal Anual (TNA)",
          "price": 0.00,
          "priceCurrency": "ARS",
          "valueAddedTaxIncluded": false
        },
        {
          "@type": "UnitPriceSpecification",
          "name": "Tasa Efectiva Anual (TEA)",
          "price": 0.00,
          "priceCurrency": "ARS",
          "valueAddedTaxIncluded": false
        },
        {
          "@type": "UnitPriceSpecification",
          "name": "Costo Financiero Total (CFT)",
          "price": 0.00,
          "priceCurrency": "ARS",
          "valueAddedTaxIncluded": true
        }
      ],
      "eligibleDuration": {
        "@type": "QuantitativeValue",
        "value": 3,
        "unitText": "MON"
      }
    },

    {
      "@type": "Organization",
      "@id": "https://www.naranjax.com/#OrgTarjetaNaranja",
      "name": "Tarjeta Naranja S.A.U.",
      "url": "https://www.naranjax.com/",
      "logo": {
        "@type": "ImageObject",
        "@id": "https://www.naranjax.com/#Logo",
        "url": "https://images.ctfassets.net/yxlyq25bynna/1IxKUBv3dtISflaWQoSIZW/11e239808ff23ee64b26ba44bfcd93a0/Logo_NX.jpeg",
        "contentUrl": "https://images.ctfassets.net/yxlyq25bynna/1IxKUBv3dtISflaWQoSIZW/11e239808ff23ee64b26ba44bfcd93a0/Logo_NX.jpeg"
      },
      "identifier": {
        "@type": "PropertyValue",
        "propertyID": "CUIT",
        "value": "30-68537634-9"
      }
    },

    {
      "@type": "WebPage",
      "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#WebPage",
      "url": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja",
      "name": "Tarjeta Naranja X",
      "description": "Solicitá tu Tarjeta Naranja X. Financiación en cuotas y Plan Z 3 cuotas sin interés.",
      "inLanguage": "es-AR",
      "isPartOf": {
        "@id": "https://www.naranjax.com/#WebSite"
      },
      "primaryImageOfPage": {
        "@id": "https://www.naranjax.com/tarjetas-de-credito/tarjeta-naranja#PaymentCardImage"
      },
      "speakable": {
        "@type": "SpeakableSpecification",
        "cssSelector": [".product-description", ".product-rates"]
      }
    }
  ]
}
```

---

## Cómo validarlo

1. Abrir https://validator.schema.org/
2. Pestaña **"Code Snippet"**
3. Pegar el JSON-LD completo (sin las triple-backticks)
4. Click **"RUN TEST"**

### Qué esperar

| Validador | Resultado esperado |
|---|---|
| validator.schema.org | ✅ 0 errors, 0 warnings |
| Google Rich Results Test | ⚠️ "PaymentCard no es un tipo elegible" — Google solo da rich results a `Product`, `Article`, `FAQPage`, `Event`, `LocalBusiness`. Para esta página el rich result se daría por el FAQPage o un envoltorio `Product`. |

### Notas sobre compatibilidad

- **`PaymentCard` no es un rich-result type de Google** — la elegibilidad de rich results la da el `Product` que envuelve la card (ya lo tenés en el builder actual) y el `FAQPage` si la página tiene preguntas.
- **`interestRate`/`annualPercentageRate`** son válidos en schema.org pero Google los ignora en SERP — sirven para entity graph y para validadores third-party (Yandex, Bing).
- **`UnitPriceSpecification` con `unitText: ANN`** es el patrón canónico para tasas anualizadas en schema.org (no está documentado en Google guidelines, sí en w3.org SDTT).

---

## Diferencias vs. lo que genera el builder actual

Builder verificado el 2026-09-25.

| Campo | Builder actual | Caso mejorado |
|---|---|---|
| `interestRate` | ❌ ausente | ✅ 84.81 % |
| `annualPercentageRate` | ❌ ausente | ✅ 102.6201 % |
| `brand` | Solo en el `Product` envoltorio | ✅ Brand "Naranja X" en el PaymentCard |
| `feesAndCommissionsSpecification` | ❌ ausente | ✅ /costos-comisiones-y-limites |
| `termsOfService` | ❌ ausente | ✅ la landing |
| `potentialAction` | ❌ ausente | ✅ ApplyAction hacia la landing |
| `audience` | ❌ ausente | ✅ PeopleAudience |
| `category` | ❌ ausente | ✅ FinancialProduct/PaymentCard |
| `offers` | 1 sola con `price: "0"` | ✅ 2 ofertas reales (cuotas + Plan Z) |
| `priceSpecification` | ❌ ausente | ✅ UnitPriceSpecification por tasa |
| `itemCondition` | ❌ ausente | ✅ NewCondition |
| `eligibleCustomerType` | ❌ ausente | ✅ Enduser |
| `eligibleDuration` | ❌ ausente | ✅ 2-9 meses |
| `seller` en Offer | ❌ ausente | ✅ ref a Organization |
| WebPage `speakable` | ❌ ausente | ✅ con cssSelector |
| `price: "0"` | ✅ presente | ✅ presente |
