# PRUD AI e-com daily — roadmap

This is a proposal, not a delivery commitment. New adapters should be accepted only after documented schemas, synthetic fixtures, regression tests and reconciliation against known totals.

| Stage | Status | Deliverables |
| --- | --- | --- |
| v0.1 | Implemented | Normalized CSV core, daily/period reports, validation, tests, docs |
| v0.2 | Proposed | Native Wildberries, Ozon and Yandex Market export adapters; Excel imports; explicit source coverage checks |
| v0.3 | Proposed | Source-specific read-only API clients, rate limits, safe credential handling, idempotent storage and reconciliation |
| v0.4 | Proposed | Local dashboard, configurable daily/weekly/monthly reports, Telegram preview and approved delivery |
| v0.5 | Proposed | Fees, logistics, refunds, cost of goods and tax-aware P&L; versioned accounting definitions |
| Later | Proposed | Megamarket, AliExpress, Amazon, eBay and Etsy adapters, inventory and stockout analytics, optional MCP interface, AI-assisted anomaly explanations with evidence and human review |

Priority is reliability before feature breadth. AI must not invent missing numbers, modify financial records without approval or transmit seller data without explicit consent. The deterministic core should remain useful without paid AI services.

Community feedback will guide adapter priorities and which fields are genuinely comparable across platforms.
