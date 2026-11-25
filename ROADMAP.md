# PRUD AI e-com daily — roadmap

This is a proposal, not a delivery commitment. New adapters should be accepted only after documented schemas, synthetic fixtures, regression tests and reconciliation against known totals.

| Stage | Status | Deliverables |
| --- | --- | --- |
| v0.1 | Implemented | Normalized CSV core, daily/period reports, validation, tests, docs |
| v0.2 | In development | Experimental WB, Ozon and Yandex Market API collectors and explicit CSV mapping implemented; native normalization, Excel imports, live verification and coverage checks pending |
| v0.3 | Proposed | Validated pagination, report downloads, source-specific native parsers, rate-limit scheduling, idempotent storage and reconciliation |
| v0.4 | Proposed | Local dashboard, configurable daily/weekly/monthly reports, Telegram preview and approved delivery |
| v0.5 | Proposed | Fees, logistics, refunds, cost of goods and tax-aware P&L; versioned accounting definitions |
| Later | Proposed | Megamarket, AliExpress, Amazon, eBay and Etsy adapters, inventory and stockout analytics, optional MCP interface, AI-assisted anomaly explanations with evidence and human review |

Priority is reliability before feature breadth. AI must not invent missing numbers, modify financial records without approval or transmit seller data without explicit consent. The deterministic core should remain useful without paid AI services.

Community feedback will guide adapter priorities and which fields are genuinely comparable across platforms.
