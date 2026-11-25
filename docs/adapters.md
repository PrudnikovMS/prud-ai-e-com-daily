# PRUD AI e-com daily — experimental marketplace adapters

## Status and boundaries

The v0.2.0 development milestone adds working request construction, bounded JSON collection and a local CSV mapping utility. Requests are opt-in, only to fixed marketplace API origins. Mock tests cover request and mapping behavior; no live seller credentials have been used. Treat all network integrations as experimental until verified against authorized test accounts. This is not a complete automatic reporting pipeline. The core remains offline by default.

The public repository contains no real seller account IDs, keys, reports, product names or delivery settings. Use a separate local deployment and read-only tokens; never send credentials in issues, screenshots or chat. Environment variables are read from the current process, never from arguments. Do not commit local output files. The private/ directory is gitignored, not encrypted. Use OS access controls and do not sync or share it.

## Collector commands

Run from the repository root with Python 3.10+. Set the applicable environment variables locally through your shell or secret manager. The source operations are read-only with respect to orders, ads, budgets and product listings; report generation and token issuance are API side effects initiated only by the explicit command. No automated retries are performed.

| Source | Operation | Environment variable names | API method |
| --- | --- | --- | --- |
| Wildberries | wb-sales | WB_ANALYTICS_TOKEN | POST /api/analytics/v3/sales-funnel/products/history |
| Wildberries | wb-expenses | WB_ADS_TOKEN | GET /adv/v1/upd |
| Wildberries | wb-ad-stats | WB_ADS_TOKEN | GET /adv/v3/fullstats |
| Ozon | ozon-sales | OZON_CLIENT_ID, OZON_API_KEY | POST /v1/analytics/data |
| Ozon | ozon-expenses | OZON_PERFORMANCE_CLIENT_ID, OZON_PERFORMANCE_CLIENT_SECRET | POST /api/client/token, GET /api/client/statistics/expense/json |
| Yandex Market | ym-orders | YANDEX_MARKET_TOKEN | POST /v2/reports/united-orders/generate |
| Yandex Market | ym-services | YANDEX_MARKET_TOKEN | POST /v2/reports/united-marketplace-services/generate |
| Yandex Market | ym-status | YANDEX_MARKET_TOKEN | GET /v2/reports/info/{reportId} |

Examples use invented identifiers. Replace dates with eligible recent dates and IDs with your own locally; do not use these examples against another seller's account.

```bash
python -m prud_ecom.adapters wb-sales --start 2026-11-20 --end 2026-11-21 --ids 101 102 --output wb-sales.json
python -m prud_ecom.adapters wb-expenses --start 2026-11-20 --end 2026-11-21 --output wb-expenses.json
python -m prud_ecom.adapters wb-ad-stats --start 2026-11-20 --end 2026-11-21 --ids 201 --output wb-ad-stats.json
python -m prud_ecom.adapters ozon-sales --start 2026-11-20 --end 2026-11-21 --limit 1000 --offset 0 --output ozon-sales.json
python -m prud_ecom.adapters ozon-expenses --start 2026-11-20 --end 2026-11-21 --output ozon-expenses.json
python -m prud_ecom.adapters ym-orders --start 2026-11-20 --end 2026-11-21 --business-id 1 --output ym-orders.json
python -m prud_ecom.adapters ym-services --start 2026-11-20 --end 2026-11-21 --business-id 1 --output ym-services.json
python -m prud_ecom.adapters ym-status --report-id demo-report --output ym-status.json
```

All responses are saved under private/ with unique filenames. No response body or credential is printed to the console. On 429/420, wait according to the provider's limits; do not loop blindly. Do not treat an empty response, a page or a missing product as a zero. Collector metadata explicitly marks coverage as unverified.

### Platform-specific reconciliation

**Wildberries.** The daily history method accepts up to 20 specified products and a recent period of up to 7 days; larger inventories need manual batching with the applicable API limits. Deleted products are not intentionally excluded. Daily history is not sufficient for net-order calculations when cancellation amounts are unavailable. Actual charge history is collected separately from campaign statistical spend. Use a verified campaign-to-SKU allocation and check charge dates/timezones; never replace actual expenses with fullstats or allocate the whole campaign cost to every SKU.

**Ozon.** The analytics endpoint returns selected metrics in the requested order; the response records that order. Use next_offset_candidate only as a paging hint, not proof of completeness. Check sorting stability, totals, duplicates and date coverage; data and subscription access may change. Optional --extra-metrics requests cancellation and return counts if available. It does not provide cancellation amounts, so do not derive net order amounts from these metrics alone. Performance expenses are campaign-level; verify units, bonuses, charge dates and product allocation separately. Authentication responses are not written to disk.

**Yandex Market.** Generating a report returns an ID, not completed data. Use ym-status with that ID after the expected generation interval and a new output filename. If the status is DONE, open the signed file link locally and download the report promptly (the link has a limited lifetime). No automatic external URL requests or ZIP extraction are performed. Keep signed links private. The order report can contain multiple transaction rows per order/SKU; services reports contain distinct fee types. Do not sum all rows as orders or all fees as ads. Filter and reconcile the exact report type and grain before mapping.

## Universal CSV normalization

The mapping command is for **already aggregated and reconciled** CSV exports; it is not an automatic parser for arbitrary native export layouts. Map columns explicitly, with constants permitted only for date, marketplace, account and currency. Do not fabricate zeros for missing financial fields. The supplied synthetic examples illustrate the complete flow:

```bash
python -m prud_ecom.adapters map-csv --kind sales --input examples/source-sales.csv --mapping examples/mapping-sales.json --output demo-sales.csv
python -m prud_ecom.adapters map-csv --kind ads --input examples/source-ads.csv --mapping examples/mapping-ads.json --output demo-ads.csv
python -m prud_ecom --sales private/demo-sales.csv --ads private/demo-ads.csv --group period --output private/demo-report.csv
```

Expected fictional result: 4 net orders, 4,000 RUB net ordered amount, 400 RUB expenses, 100 RUB cost per net order, 10% ad spend / net ordered amount. The core validates joined keys, duplicates and metrics. See [schema.md](schema.md) for the mandatory cancellation cohort and spend allocation rules.

## References checked during development (2026-11-25)

- WB [official developer portal](https://dev.wildberries.ru/), [analytics specification mirror](https://dev.wildberries.cn/docs/openapi/analytics), [promotion specification mirror](https://dev.wildberries.cn/docs/openapi/promotion); [daily history](https://valeryverkhoturov.github.io/wb-api-client-docs/reference/api/analytics/post-api-analytics-v3-sales-funnel-products-history), [cost history](https://valeryverkhoturov.github.io/wb-api-client-docs/reference/api/promotion/get-adv-v1-upd), [campaign statistics](https://valeryverkhoturov.github.io/wb-api-client-docs/reference/api/promotion/get-adv-v3-fullstats).
- Ozon [official developer portal](https://dev.ozon.ru/), [analytics change notice](https://dev.ozon.ru/news/252-Izmeneniia-v-rabote-metoda-v1-analytics-data/), [Seller API](https://docs.ozon.ru/api/seller/), [Performance API](https://docs.ozon.ru/api/performance/); third-party reference snapshots [analytics request](https://github.com/etozhearut/ozon-seller-api/blob/main/docs/52-premium.md), [Performance OpenAPI](https://github.com/MissiaL/ozon-api/blob/main/references/ozon-performance-openapi.json). Current official endpoint details could not all be retrieved; confirm against your account's current docs before production use.
- Yandex Market [authentication](https://yandex.ru/dev/market/partner-api/doc/ru/concepts/api-key), [orders](https://yandex.ru/dev/market/partner-api/doc/ru/reference/reports/generateUnitedOrdersReport), [services](https://yandex.ru/dev/market/partner-api/doc/en/reference/reports/generateUnitedMarketplaceServicesReport), [report status](https://yandex.ru/dev/market/partner-api/doc/ru/reference/reports/getReportInfo).

No external source code or credentials were copied into this repository. API contracts can change. Contributions with fictional, documented fixtures are welcome.
