# PRUD AI e-com daily

**Open-source, local-first marketplace reporting for sellers, analysts and developers worldwide.**

[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3.0-blue.svg)](LICENSE)
[![CI](https://github.com/PrudnikovMS/prud-ai-e-com-daily/actions/workflows/ci.yml/badge.svg)](https://github.com/PrudnikovMS/prud-ai-e-com-daily/actions/workflows/ci.yml)

[Русская документация](docs/README.ru.md) · [Data schema](docs/schema.md) · [Roadmap](ROADMAP.md) · [Contributing](CONTRIBUTING.md)

## Why this project exists

Marketplace sellers spend valuable time reconciling orders, cancellations and advertising expenses across inconsistent reporting formats. PRUD AI e-com daily aims to make routine analytics accessible, reproducible and trustworthy, without requiring a paid analytics subscription or sending seller data to a third party.

The project is developed by a marketplace practitioner. This repository contains an independent public reporting core, not a production deployment or customer database. All example accounts, SKU identifiers, campaigns and transaction values are fictional.

## What works in v0.1.0

- Import two normalized CSV files: daily SKU-level orders and campaign-level advertising expenses.
- Reconcile by date, marketplace, seller account, currency and SKU.
- Detect duplicate sales records, duplicate campaigns, invalid values and incomplete joins.
- Calculate gross and net orders, ordered amounts after cancellations, advertising spend, blended cost per net order and ad spend as a percentage of net ordered amount.
- Aggregate by SKU/day, seller/day or seller/period with weighted ratios; keep currencies separate.
- Export Excel-compatible UTF-8 CSV, without API keys, external services or runtime dependencies.
- Stop on incomplete joins rather than silently inventing zero values.

**Scope:** normalized CSV input only. Native marketplace exports must be mapped into the documented schema manually or through a future adapter. Live API connections, AI-generated recommendations, Telegram delivery, financial P&L and scheduling are planned, not implemented in this release. This tool reports order metrics, not realized revenue or profit. It cannot independently prove that every expected date/SKU is present in both sources.

## Marketplace coverage

| Marketplace | Normalized CSV | Native export / API |
| --- | --- | --- |
| Wildberries | Synthetic example | Planned |
| Ozon | Synthetic example | Planned |
| Yandex Market | Synthetic example | Planned |
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

## Tests

```bash
python -m unittest discover -s tests -v
```

Regression tests cover aggregation, zero-order spending, duplicates, missing data, currency separation and invalid input. No test contacts a real marketplace.

## Privacy and security

The reporting core operates locally, reads files you specify, and does not make network requests. Use synthetic examples in public issues. Never commit seller exports, account identities, credentials or Telegram tokens. See [SECURITY.md](SECURITY.md). CSV input is expected to contain trusted business identifiers; inspect unfamiliar CSV text before opening it in a spreadsheet.

## Help shape the project

Marketplace sellers and developers are welcome to suggest report mappings, contribute synthetic format fixtures, report calculation edge cases, and review metric definitions. Please consult the [roadmap](ROADMAP.md) and [contribution guide](CONTRIBUTING.md).

## License and independence

Copyright © 2026 PrudnikovMS. The source code in this public repository is distributed under [GNU AGPL-3.0-only](LICENSE). The AGPL permits commercial use, subject to its terms including applicable source-code obligations. The license covers only material published under it; it does not provide access to any separate service, private data, credentials or infrastructure. No trademark rights are granted by the software license.

This project is unaffiliated with any marketplace or AI provider. Marketplace names identify potential data sources only.
