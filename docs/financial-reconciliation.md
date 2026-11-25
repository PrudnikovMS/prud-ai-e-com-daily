# Financial reconciliation design — PRUD AI e-com daily

**Proposed design, not implemented.** This document defines development goals and acceptance criteria, not an accounting guarantee. Marketplace-specific fields, tax treatment and accounting methods must be verified against official documentation and authorized sample reports before implementation. Do not use the current v0.2 reporting core to calculate actual profit.

## 1. Why reconciliation matters

A sales funnel describes demand and order activity. Advertising statistics describe campaign activity; actual charges can differ because of timing, bonuses or adjustments. A detailed official financial statement records realized transactions, services, fees and adjustments. Payouts are cash movements, not revenue. These are different views of business activity. A seller needs consistent, traceable bridges between them, not a total obtained by adding every number in every tab.

## 2. Proposed source contract

| Source | Main use | Important distinction |
| --- | --- | --- |
| Sales funnel / orders | Operational orders, cancellations and conversion | Order-cohort metrics; not realized revenue |
| Advertising statistics | Campaign performance, clicks and attributed orders | Statistical spend is not automatically an actual charge |
| Actual advertising charge history | Reconcile advertising expense and charge adjustments | Match against financial statement deductions; do not count twice |
| Official detailed financial report | Recognized sales, returns, commissions, logistics, storage, penalties, deductions and compensation | Preserve original sign, type, dates, IDs and corrections |
| Settlement / payout report | Amounts payable, transfers, balances | Cash timing may differ from recognition |
| Seller-entered cost history | Cost of goods sold and returned stock | SKU, effective date, quantity, currency, cost method |
| Seller-entered expenses and tax settings | Expenses not already included in marketplace statements | Explicit tax basis and expense scope |
| Inventory and stock movements (future) | Stock reconciliation, purchases and shortages | Stock purchase is not automatically COGS |

Store each imported source as an immutable or versioned snapshot locally, with source type, marketplace, seller account alias, schema version, currency, timezone, reporting range, retrieval timestamp, row identifiers, and completeness state. Never expose real snapshots in the public repository. Track data lineage from each derived amount back to original rows.

## 3. Financial event normalization

Create a canonical event representation with source document ID, source row ID (or documented stable key), event type, order/transaction/SKU identifiers when available, quantity, signed amount, currency, order date, recognition date, charge date and settlement date as applicable. Classify source events via versioned, marketplace-specific rules.

Use Decimal rather than floating point for money. Maintain independent account, currency and period dimensions. Do not silently merge currencies or use one marketplace's definitions for another. Keep original raw signs and amounts; normalize signs through explicit rules. Unknown event types, missing identifiers and ambiguous mappings enter a review queue, not a guessed category.

Prefer stable source row IDs for deduplication. Reimporting the same snapshot must not multiply amounts. New revisions must supersede or adjust earlier results with auditable history. Handle deleted SKUs and historical catalog mappings; missing catalog metadata is not proof that a financial transaction is invalid.

## 4. Reconciliation pipeline (planned)

1. Acquire official data through authorized APIs or seller-exported files. Validate schema, dates, pages, report status, currency and coverage. Retain raw source totals and hashes.
2. Normalize operational and financial records separately. Use source-specific definitions for order, fulfillment, realized sale, return and charge date. Never treat all order events as sales.
3. Reconcile recognized transactions to official report totals by source-defined amount type; separately bridge order cohorts to completed sales and returns, including pending fulfillment, cancellations and timing differences.
4. Reconcile actual advertising charges with financial deductions by explicit references or documented allocation rules. If a fee is already embedded in net settlement, do not subtract it twice. Keep unallocated expenses at account level until a justified allocation is possible.
5. Join recognized quantities to historical SKU costs. For missing or ambiguous cost, show an incomplete result and the affected quantities. Do not assume zero cost or reconstruct historical costs from today's price.
6. Calculate P&L and unit economics from classified events; show recognized revenue, COGS, expense breakdown, adjustments and applicable taxes according to the configured accounting basis.
7. Independently reconcile marketplace payable balances and actual payouts. Show open amounts, holds, timing differences and transfers; do not equate payout to profit.
8. Produce traceable results and a discrepancy report; retain the source references, ruleset version, coverage state and revision timestamp.

Reconcile by report-native totals first. For each comparable category, discrepancy = source control total minus normalized equivalent total (same scope, currency, signs and period). Nonzero discrepancies remain visible even if within a documented rounding tolerance. An incomplete source is not verified even if its partial totals happen to match. An amount not attributable to SKU may remain in a clearly identified account-level bucket.

## 5. Product cost and accounting basis

Plan a local product-cost table keyed by marketplace/account/SKU or an explicit shared product mapping, with currency, effective date range, cost amount per unit, cost method and source notes. The seller supplies the data. Support historical changes; prevent overlapping or ambiguous cost periods. Decide the cost method (for example a documented effective-dated unit cost first, batch-based FIFO or weighted average only after inventory support exists). For recognized sales use the cost applicable under the chosen method; returns reverse the original cost only when the inventory/return treatment justifies it. Damaged/lost goods and stock write-offs need explicit handling. Never claim an effective-dated estimate is audited inventory valuation.

For every P&L calculation define the recognition basis, treatment of tax/VAT, fees and compensation, currency, period, return handling and allocation policy. The illustrative shape is recognized net sales plus other recognized income, minus recognized COGS and distinct operating expense categories; add financial costs and configured taxes only under a documented policy. Marketplace net transfers must not be mixed with gross revenue or already-netted fees. Do not label an incomplete subtotal as net profit.

## 6. Intended reports and interface

- Orders and advertising: operational metrics; distinguish all-order blended ratios from ad-attributed metrics.
- Financial reconciliation: official totals versus normalized amounts, unmatched records, missing pages, timing bridges and adjustments.
- Product costs: editable history with validation; flag missing historical cost.
- P&L and unit economics: amount by SKU, account, currency and period, account-level unallocated costs and a drill-down to source events.
- Settlements: payout and payable reconciliation; separate cash view.
- Inventory and purchasing: future stock/cost flows.
- Dashboard and delivery: draft versus reconciled status, daily/weekly/monthly reporting, export and optional approved Telegram delivery.
- AI assistance: optional explanations backed by deterministic results; no invented numbers or autonomous financial changes.

Status values proposed: DRAFT (missing or provisional inputs), NEEDS_REVIEW (discrepancy or uncertain mapping), RECONCILED (defined source controls matched and coverage checked), REVISED (new source version or correction, requiring revalidation). Financial review and correctness are not guaranteed by a status alone. Do not present verified calculations without the source scope and timestamp.

## 7. Acceptance fixtures and failure cases

Use synthetic fixtures with independently calculated expected results. Cover order with cancellation; sale and late return; ad charge present in two sources; campaign spanning multiple SKUs; advertising with zero orders; cost change during period; return tied to historical cost; missing SKU cost; fee corrections; negative adjustments; closed-month revisions; deleted SKU; duplicate import; missing page; currency separation; unknown charge type; marketplace payouts across period boundaries. Test intermediate controls as well as final totals. For live API compatibility, use only authorized test accounts and keep all outputs private.

The first implementation target is Wildberries. Ozon and Yandex Market require their own financial event dictionaries, adapters and acceptance tests. Other marketplaces are not yet integrated. The public repository uses only independently developed code, permitted official API access and synthetic examples.
