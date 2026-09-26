# Auditoría de schemas — propiedades faltantes

**Fecha de la auditoría:** 2026-06-14. **Estado verificado contra el código:** 2026-09-25.
**Vocabulario de referencia:** [schema.org v30.0](https://schema.org/version/30.0/).
**Alcance:** los 9 builders de [src/schema_automation/schema/](../../src/schema_automation/schema/), comparados con las propiedades disponibles en el vocabulario.

Las reglas de modelado que ya aplica el código están en [reglas-jsonld.md](../reglas-jsonld.md). Esta auditoría lista solo lo que falta.

---

## Resumen

Props = propiedades que emite hoy el nodo principal / propiedades disponibles en v30.0.

| Builder | Archivo | Props | Faltante principal |
|---|---|---|---|
| `PaymentCard` | [payment_card.py](../../src/schema_automation/schema/payment_card.py) | 8/46 | `interestRate`, `annualPercentageRate` |
| `LoanOrCredit` | [loan.py](../../src/schema_automation/schema/loan.py) | 13/50 | `feesAndCommissionsSpecification`, `termsOfService` |
| `BankAccount` | [bank_account.py](../../src/schema_automation/schema/bank_account.py) | 6/44 | `bankAccountType` |
| `PaymentService` | [payment_service.py](../../src/schema_automation/schema/payment_service.py) | 7/42 | `availableChannel`, `hoursAvailable` |
| `FinancialProduct` | [financial_product.py](../../src/schema_automation/schema/financial_product.py) | 8/41 | `interestRate`, `annualPercentageRate` |
| `InvestmentOrDeposit` | [investment.py](../../src/schema_automation/schema/investment.py) | 11/42 | `annualPercentageRate` |
| `InsuranceAgency` | [insurance.py](../../src/schema_automation/schema/insurance.py) | 8/128 | `telephone`, `email`, `openingHoursSpecification` |
| `BlogPosting` | [blog.py](../../src/schema_automation/schema/blog.py) | 11/137 | `articleSection`, `author` como `Person` |
| `Event` | [event.py](../../src/schema_automation/schema/event.py) | 11/56 | `sponsor`, `subEvent` |

---

## Faltantes transversales

1. **`brand` en el nodo financiero.** El `Product` envoltorio ya lleva `brand`. Los nodos `PaymentCard`, `LoanOrCredit`, `BankAccount`, `PaymentService`, `FinancialProduct` e `InvestmentOrDeposit` no.
2. **`termsOfService` y `feesAndCommissionsSpecification`.** Ningún builder los emite. Aplican a productos regulados por el BCRA, sobre todo `PaymentCard` y `LoanOrCredit`. Destinos en [reglas-jsonld.md](../reglas-jsonld.md#referencias-entre-nodos).
3. **`potentialAction`.** Ningún builder lo emite. Candidato: `ApplyAction` en préstamos y tarjetas.
4. **`audience`.** Solo lo lleva `InvestmentOrDeposit`. Aplica a productos segmentados (monotributistas, jubilados).
5. **Reviews.** No se agregan `aggregateRating` ni `review` sin reviews reales (ver [reglas-jsonld.md](../reglas-jsonld.md#datos-que-no-se-inventan)).

---

## Faltantes por builder

### PaymentCard
- `interestRate` y `annualPercentageRate` (TNA y CFT). Requieren tasas vigentes de la letra chica.
- `feesAndCommissionsSpecification`, `termsOfService`, `category`.

### LoanOrCredit
Ya emite `loanType`, `interestRate` y `annualPercentageRate`.
- `gracePeriod`, `requiredCollateral`, `recourseLoan`, `renegotiableLoan`.
- `feesAndCommissionsSpecification`, `termsOfService`.

### BankAccount
- `bankAccountType`. Es lo que diferencia Caja de Ahorro, Cuenta en Dólares y Cuenta Remunerada. Hoy solo cambia el `name`.
- `termsOfService`, `category`.

### PaymentService
- `availableChannel` (app, web, presencial) y `hoursAvailable`.
- `termsOfService`.

### InvestmentOrDeposit
Ya emite `interestRate`.
- `annualPercentageRate`, `feesAndCommissionsSpecification`.

### InsuranceAgency
- `telephone`, `email` y `openingHoursSpecification`. Google los pide para `LocalBusiness`.
- `sameAs`, `slogan`.

### BlogPosting
Ya emite `articleBody`, `wordCount` e `inLanguage`.
- `articleSection` y `keywords`.
- `author` es hoy `#OrgNaranjaX`. Debería ser un `Person` con `url` y `sameAs` cuando el artículo tenga autor.
- `speakable`.

### Event
Ya exige `startDate`.
- `sponsor`, `subEvent` (sub-promociones por categoría), `keywords`.

### Offer (compartido)
Emite 15 de 67 propiedades en el conjunto de builders.
- `eligibleCustomerType`. Distingue monotributista de consumidor final.
- `itemCondition`.
- `eligibleDuration` fuera de `investment_or_deposit`.

### Product (envoltorio)
Emite 7 de 72 propiedades. Ya lleva `brand`; `category` solo en `insurance_agency`.
- `category` en el resto, `audience`.

### FAQPage y WebPage
Ya emiten `inLanguage`. Falta `speakable`.

---

## Problemas de consistencia vigentes

1. **`provider` con forma distinta.** Es una lista en `PaymentCard` y `LoanOrCredit`, y un objeto en `BankAccount`, `PaymentService`, `FinancialProduct` e `InvestmentOrDeposit`.
2. **`VALID_SCHEMA_TYPES` fijo** en [validator.py](../../src/schema_automation/validation/validator.py). Se desincroniza cuando un builder agrega un tipo. La alternativa es validar contra `schemaorg-current-https.jsonld`.

---

## Prioridades

| Prioridad | Cambio | Esfuerzo |
|---|---|---|
| P0 | `brand` en nodos financieros | Bajo |
| P0 | `interestRate` / `annualPercentageRate` en `PaymentCard`, `FinancialProduct` e `InvestmentOrDeposit` | Medio (requiere tasas vigentes) |
| P0 | `bankAccountType` en `BankAccount` | Bajo |
| P0 | Unificar la forma de `provider` | Bajo |
| P1 | `telephone`, `email`, `openingHoursSpecification` en `InsuranceAgency` | Bajo |
| P1 | `articleSection` y `author` como `Person` en `BlogPosting` | Medio (parsing) |
| P1 | `potentialAction` (`ApplyAction`) en productos crediticios | Medio |
| P1 | `termsOfService` y `feesAndCommissionsSpecification` | Bajo |
| P2 | `audience` segmentado | Bajo |
| P2 | `speakable` en `BlogPosting`, `FAQPage` y `WebPage` | Bajo |
| P2 | `itemCondition` en `Offer` | Bajo |
| P2 | Validador contra el vocabulario oficial | Alto |
