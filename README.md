# PRUD AI e-com daily

**Open-source, local-first marketplace analytics and financial reconciliation for sellers, analysts and developers.**

> **Early development / prototype (v0.2.0).** This project is incomplete, experimental and not ready for production accounting. The current reporting core calculates operational order metrics from normalized CSV files. It does not yet reconcile official financial reports, calculate actual profit or automatically produce complete reports from marketplace APIs. Please do not rely on it for business-critical financial decisions without independent verification.

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![CI](https://github.com/PrudnikovMS/prud-ai-e-com-daily/actions/workflows/ci.yml/badge.svg)](https://github.com/PrudnikovMS/prud-ai-e-com-daily/actions/workflows/ci.yml)

[Русская документация](docs/README.ru.md) · [Data schema](docs/schema.md) · [Financial reconciliation design](docs/financial-reconciliation.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md) · [Development tasks](https://github.com/PrudnikovMS/prud-ai-e-com-daily/issues)

## Why this project exists

Marketplace sellers spend valuable time reconciling orders, cancellations and advertising expenses across inconsistent reporting formats. PRUD AI e-com daily aims to make routine analytics accessible, reproducible and trustworthy, without requiring a paid analytics subscription or sending seller data to a third party.

The maintainer works in marketplace management and financial analytics. The idea grew out of hands-on work with Wildberries sales-funnel reports and advertising expenses. The original experience covers basic WB reporting, not a complete financial reconciliation system. Development capacity is currently limited; the project is being built incrementally. This repository contains an independently developed public reporting core, not a private production deployment or customer database. All example accounts, SKU identifiers, campaigns and transaction values are fictional.

## Long-term goal: one reconciled source of truth

Many sellers must compare sales funnels, advertising reports, official financial statements, returns, fees, logistics, payouts and their own cost data manually. The aim is to connect these reports while preserving their different accounting meanings, rather than blindly adding totals from different sources.

The planned architecture separates three views: operational analytics (orders, cancellations and advertising), recognized financial results (official settlement transactions, fees, cost of goods and external expenses), and cash movements (payouts and balances). These views must reconcile through documented rules and retain source references, periods and discrepancies.

The seller should be able to enter SKU-level cost of goods with effective dates, record external expenses and configure relevant tax assumptions. The system should then calculate transparent P&L and unit economics from reconciled financial events, clearly distinguishing provisional, incomplete and verified results. Official financial statements should be the reference for recognized marketplace charges and settlements; operational orders are not recognized revenue. Duplicate advertising charges, late returns, adjustments, period boundaries and unallocated expenses must be handled explicitly.

Proposed modules: official report import and reconciliation; sales and advertising; cost of goods; P&L and unit economics; payouts; inventory and purchasing; dashboard; scheduled reporting and optional Telegram delivery; evidence-based AI assistance. None of these proposed extensions should be treated as complete simply because they are described here. See the [financial reconciliation design](docs/financial-reconciliation.md).

## Current status versus planned functionality

| Capability | Status |
| --- | --- |
| Normalized CSV orders/advertising calculations and validation | Implemented; synthetic tests |
| Wildberries sales funnel and ad expense collection | Experimental public API collectors; live public integration not verified |
| Ozon and Yandex Market collection | Experimental request scaffolding only; end-to-end integrations not implemented |
| Official financial report import and reconciliation | Planned |
| Effective-dated product costs, P&L and unit economics | Planned |
| Payout reconciliation, inventory, dashboard, scheduled delivery | Planned |
| Other marketplaces and AI-assisted explanations | Planned |

The maintainer intends to use AI-assisted development, including Codex if available, for adapter implementation, financial regression tests, security review, documentation and release maintenance. Development tools can accelerate the work, but accounting definitions and results require human review. No funding, program acceptance, community adoption or completed feature is claimed here.

## What is implemented in v0.2.0

- Import two normalized CSV files: daily SKU-level orders and campaign-level advertising expenses.
- Reconcile by date, marketplace, seller account, currency and SKU.
- Detect duplicate sales records, duplicate campaigns, invalid values and incomplete joins.
- Calculate gross and net orders, ordered amounts after cancellations, advertising spend, blended cost per net order and ad spend as a percentage of net ordered amount.
- Aggregate by SKU/day, seller/day or seller/period with weighted ratios; keep currencies separate.
- Export Excel-compatible UTF-8 CSV, without API keys, external services or runtime dependencies.
- Stop on incomplete joins rather than silently inventing zero values.

**Scope:** the reporting core still requires normalized CSV. Experimental API collectors for WB, Ozon and Yandex Market now retrieve source data or request reports; they do not yet produce reconciled net-order reports directly. Explicit CSV column mapping is available for already aggregated exports. Live-account validation, native normalization, AI-generated recommendations, Telegram delivery, financial P&L and scheduling remain outstanding. This tool reports order metrics, not realized revenue or profit. It cannot independently prove that every expected date/SKU is present in both sources.

## Marketplace coverage

| Marketplace | Normalized CSV | Native export / API |
| --- | --- | --- |
| Wildberries | Synthetic example | Experimental sales history, actual expenses, ad statistics |
| Ozon | Synthetic example | Experimental sales analytics and Performance expenses |
| Yandex Market | Synthetic example | Experimental orders/services report generation and status |
| Amazon | Synthetic example | Planned |
| Megamarket, AliExpress, eBay, Etsy and others | Generic schema | Proposed |

Any marketplace can be represented by a source identifier if its data can be accurately mapped into the schema. The examples are fabricated and do not certify compatibility with marketplace-native report formats.

## Quick start

Python 3.10+; no third-party runtime dependencies. Clone or download this repository, then run from its root:

```bash
git clone https://github.com/PrudnikovMS/prud-ai-e-com-daily.git
cd prud-ai-e-com-daily
python -m prud_ecom --sales examples/sales.csv --ads examples/ads.csv --group period --output output.csv
```

On Windows, `py -3` may be used instead of `python`. Open `output.csv` in a spreadsheet application. For individual daily SKU rows, use `--group sku`; for daily account totals, use `--group daily`. Use `--start YYYY-MM-DD --end YYYY-MM-DD` to filter a period.

Example output (fictional Wildberries account, two days):

| Net orders | Net ordered amount | Ad spend | Cost per net order | Ad spend / net amount |
| ---: | ---: | ---: | ---: | ---: |
| 16 | 16,000 RUB | 1,700 RUB | 106.25 RUB | 10.63% |

These ratios use all orders in the selected group, not ad-attributed orders. Zero denominators produce empty ratio cells; spending is still reported. See [the schema](docs/schema.md) for the cancellation cohort and allocation assumptions.

## Experimental marketplace adapters

Read [the adapter setup guide](docs/adapters.md) or [русскую инструкцию](docs/adapters.ru.md). Use `python -m prud_ecom.adapters --help` for commands. Source collection is explicitly invoked, local credentials only, with raw outputs kept in the ignored `private/` folder. No live seller account has been tested. The original report command remains offline. Never mistake raw campaign data for verified SKU-level spending.

## Tests

Passing synthetic tests verifies selected code behavior, not live API compatibility or accounting accuracy. Financial reconciliation needs its own independently checked reference fixtures and acceptance tests.

```bash
python -m unittest discover -s tests -v
```

Regression tests cover aggregation, zero-order spending, duplicates, missing data, currency separation and invalid input. No test contacts a real marketplace.

## Privacy and security

The reporting core operates locally and makes no network requests. Experimental collectors contact only the selected marketplace API when explicitly invoked. Raw responses remain local. Use synthetic examples in public issues. Never commit seller exports, account identities, credentials or Telegram tokens. See [SECURITY.md](SECURITY.md). CSV input is expected to contain trusted business identifiers; inspect unfamiliar CSV text before opening it in a spreadsheet.

## Help shape the project

Marketplace sellers, analysts and developers are invited to review the proposed reconciliation rules, suggest official report mappings, contribute synthetic format fixtures and report calculation edge cases. The first priority is trustworthy Wildberries accounting; other marketplaces follow only after their source contracts and calculations have been validated. Community feedback will determine priorities. Please consult the [roadmap](ROADMAP.md) and [contribution guide](CONTRIBUTING.md).

## License and independence

Copyright © 2026 PrudnikovMS. The source code in this public repository is distributed under [GNU AGPL-3.0-only](LICENSE). The AGPL permits commercial use, subject to its terms including applicable source-code obligations. The license covers only material published under it; it does not provide access to any separate service, private data, credentials or infrastructure. No trademark rights are granted by the software license.

This project is unaffiliated with any marketplace or AI provider. Marketplace names identify potential data sources only.
