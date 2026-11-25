# Normalized data contract

Use comma-separated UTF-8 CSV, optionally with a BOM. Header order is flexible, but the exact column set is required. Every field must be non-empty. Decimal separator is a dot; amounts have up to two decimal places. Counts are nonnegative integers. The current core does not support signed corrections or currencies with more than two decimal places.

## Sales CSV

`date,marketplace,account,currency,sku,orders,cancelled_orders,ordered_amount,cancelled_amount`

The first five fields form a unique daily SKU key. Dates use ISO YYYY-MM-DD. Marketplace identifiers are normalized to lowercase, currency identifiers to uppercase; account and SKU identifiers are case-sensitive. Use consistent IDs across all inputs. Identifiers beginning with `=`, `+`, `-`, or `@`, or containing control characters, are rejected to reduce spreadsheet formula injection risk; map them to safe IDs upstream. Currency is a three-letter code, not validated against a currency registry. Choose a consistent business timezone before normalizing dates.

The sales source must provide gross orders and cancellation counts/amounts attributed to that same order cohort. Amounts must use consistent tax, discount and currency definitions. Late cancellations may require re-exporting a period. Sources that report cancellations by event date rather than order cohort must not be imported unchanged. Cancellation counts and amounts cannot exceed gross counts and amounts.

## Advertising CSV

`date,marketplace,account,currency,sku,campaign_id,ad_spend`

A key plus campaign_id must be unique. Consolidate repeated campaign rows upstream and use consistent attribution/allocation rules. Spend for a multi-SKU campaign must be allocated by the source or documented upstream; do not duplicate a whole campaign total across SKUs. When a SKU has confirmed zero ad spend, provide a zero row (for example campaign_id `no_ads`). If a SKU incurs spend but has confirmed zero orders, provide a zero sales row. Never manufacture a zero when the source is missing. If an expense cannot be allocated to a SKU, resolve the mapping before import.

The join requires identical sets of keys. This catches unmatched data, not omissions shared by both files. Reconcile upstream file coverage and source totals independently. An entirely empty date range produces an error. Date filters only validate and aggregate included records, apart from basic structural and date/key checks.

## Derived metrics

- Net orders = orders − cancelled_orders.
- Net ordered amount = ordered_amount − cancelled_amount.
- Advertising spend = sum of campaign spending.
- Blended cost per net order = advertising spend / net orders.
- Advertising spend percentage = advertising spend / net ordered amount × 100.

Ratios are calculated after summing the underlying values, not by averaging row ratios. Blank ratio means the denominator is zero; 0.00 means a defined zero ratio. Decimal rounding is half-up at display precision. No FX conversion is performed. Marketplace/account/currency keys stay separate, so there is no mixed-currency grand total. This is not a profit-and-loss statement or an ad attribution model.
