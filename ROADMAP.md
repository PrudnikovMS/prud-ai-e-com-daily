# PRUD AI e-com daily — development roadmap / план развития

**Status: early development, v0.2.0 prototype.** This is an intended six-month development horizon, not a promised release schedule. Progress depends on maintainer capacity, access to authorized test sources, documented marketplace contracts and validation results. Do not infer features from version numbers.

## Already implemented / уже реализовано

- v0.1: offline normalized CSV reporting core, operational order/ad metrics, validation, synthetic examples.
- v0.2 (experimental): bounded API collectors for WB, Ozon and Yandex Market; explicit CSV column mapping; local output and mock tests.
- Not yet implemented: complete financial ingestion, recognized revenue and payout reconciliation, cost-of-goods accounting, verified P&L, native end-to-end integrations, dashboard and autopilot.

## Six-month development direction / ориентир на шесть месяцев

| Phase | Planned work | Acceptance gate |
| --- | --- | --- |
| Month 1 — WB source reconciliation / сверка WB | Official detailed financial and settlement reports; funnel and ads reconciliation; native CSV/XLSX parsing; coverage, pagination, corrections, duplicate protection | Source totals and signed movements reconcile on independently calculated synthetic reference cases; incomplete periods are explicit |
| Month 2 — product cost and P&L / себестоимость и ОПиУ | Effective-dated SKU costs, historical costs, realized sales and returns, commission, logistics, storage, ads, other fees, external expenses, explicit tax assumptions; unit economics | Every result traceable to inputs, no double charges, missing cost never treated as zero; payout reconciliation separate |
| Month 3 — Ozon | Implement native official financial/settlement, sales and ad inputs, source-specific mappings and verified calculations | Source-to-report fixtures and authorized test results; no premature claim of production support |
| Month 4 — Yandex Market / Яндекс Маркет | Complete report lifecycle and download handling, transactions and services, payout and advertising reconciliation | Reconcile source totals with documented classifications and test period revisions |
| Month 5 — seller workflow / интерфейс и автопилот | Local UI, manual cost/expense entry, SKU/account/period views, diagnostics, daily/weekly/monthly summaries, Excel/CSV, optional Telegram preview and delivery | Missing/incomplete data clearly visible; no duplicate delivery; local credentials; integration tests |
| Month 6 — quality and community / качество и сообщество | Security review, install guide, public feedback, documented releases, optional AI-assisted anomaly explanations, prioritize additional marketplace adapters | Reproducible installation and tests; human-reviewed financial formulas; record actual user feedback when available |

Additional marketplaces (Amazon, eBay, Etsy, AliExpress, Megamarket and others), inventory, stockout and purchasing analysis are future extensions. Their inclusion is subject to documented and permitted official data access. Cross-marketplace accounting must respect source-specific definitions, currencies and reporting periods.

## Engineering principles

- Preserve the source, reporting period, timezone, currency, source revision and provenance.
- Use official marketplace financial reports as the reference for recognized financial charges, not a sales funnel or an ad attribution report.
- Keep operational metrics, financial results and cash settlements distinct; reconcile instead of summing them.
- Make discrepancies, missing cost, uncertain allocations and incomplete source coverage visible; do not invent zeros.
- Use deterministic Decimal-based financial calculations with documented rounding and regression fixtures.
- AI may help maintain the code and explain verified data; it must not invent figures or act on seller accounts.
- Publish only independent code, public documentation references and fictional fixtures. Never publish customer data, credentials, private integration details or restricted materials.
- Treat every new marketplace as experimental until verified. A passing mock test is not live validation.

## Contribution priorities / как помочь

See the [financial reconciliation design](docs/financial-reconciliation.md), [русский проект методологии](docs/financial-reconciliation.ru.md) and [issue tracker](https://github.com/PrudnikovMS/prud-ai-e-com-daily/issues). Contributions are welcome, especially anonymization-safe synthetic fixtures, source contract descriptions and independently checked expected financial outcomes.

AI-assisted development may improve maintainer throughput, testing and documentation. The project does not claim financial support, approval from any provider, or adoption metrics that have not been measured.
