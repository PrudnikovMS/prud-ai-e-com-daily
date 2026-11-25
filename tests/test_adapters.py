# SPDX-License-Identifier: AGPL-3.0-only
import io
import json
import tempfile
import unittest
from pathlib import Path

from prud_ecom.adapters import (AdapterError, collect, map_csv, parser, save_private,
                                WB_ANALYTICS, WB_ADS, OZON_SELLER, OZON_PERFORMANCE, YANDEX)
from prud_ecom.report import SALES, ADS, build_report


class FakeAPI:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []
    def __call__(self, base, path, **kwargs):
        self.calls.append((base, path, kwargs))
        return self.responses.pop(0)


ENV = {"WB_ANALYTICS_TOKEN": "test-only", "WB_ADS_TOKEN": "test-only",
       "OZON_CLIENT_ID": "123", "OZON_API_KEY": "test-only",
       "OZON_PERFORMANCE_CLIENT_ID": "test-only", "OZON_PERFORMANCE_CLIENT_SECRET": "test-only",
       "YANDEX_MARKET_TOKEN": "test-only"}
DATES = ["--start", "2026-11-20", "--end", "2026-11-21", "--output", "mock.json"]


class Adapters(unittest.TestCase):
    def run_fake(self, op, fake, *extra):
        return collect(parser().parse_args([op, *DATES, *extra]), env=ENV, transport=fake)

    def test_wb_sales(self):
        f = FakeAPI([{"product": {"nmId": 101}, "history": [{"date": "2026-11-20", "orderCount": 2}]}])
        result = self.run_fake("wb-sales", f, "--ids", "101")
        self.assertEqual(result[0]["history"][0]["orderCount"], 2)
        base, path, req = f.calls[0]
        self.assertEqual(base, WB_ANALYTICS)
        self.assertEqual(path, "/api/analytics/v3/sales-funnel/products/history")
        self.assertFalse(req["body"]["skipDeletedNm"])
        self.assertEqual(req["body"]["aggregationLevel"], "day")

    def test_wb_expenses_separate_from_statistical_spend(self):
        f = FakeAPI([{"advertId": 1, "updSum": 30}])
        self.run_fake("wb-expenses", f)
        self.assertEqual(f.calls[0][0:2], (WB_ADS, "/adv/v1/upd"))
        f = FakeAPI([])
        self.run_fake("wb-ad-stats", f, "--ids", "1")
        self.assertEqual(f.calls[0][1], "/adv/v3/fullstats")

    def test_wb_duplicate_ids_rejected_before_request(self):
        f = FakeAPI([])
        with self.assertRaises(AdapterError):
            self.run_fake("wb-sales", f, "--ids", "101", "101")
        self.assertEqual(f.calls, [])

    def test_missing_token(self):
        f = FakeAPI([])
        with self.assertRaises(AdapterError):
            collect(parser().parse_args(["wb-expenses", *DATES]), env={}, transport=f)
        self.assertEqual(f.calls, [])

    def test_ozon_sales_order_and_pagination(self):
        f = FakeAPI({"result": {"data": [{"dimensions": [{"id": "101"}, {"id": "2026-11-20"}], "metrics": [3, 300]}]}})
        r = self.run_fake("ozon-sales", f, "--limit", "1")
        self.assertEqual(f.calls[0][0:2], (OZON_SELLER, "/v1/analytics/data"))
        self.assertEqual(r["metric_order"], ["ordered_units", "revenue"])
        self.assertEqual(r["next_offset_candidate"], 1)
        self.assertFalse(r["coverage_verified"])

    def test_ozon_invalid_metrics(self):
        f = FakeAPI({"result": {"data": [{"dimensions": [], "metrics": [3]}]}})
        with self.assertRaises(AdapterError):
            self.run_fake("ozon-sales", f)

    def test_ozon_expense_token_not_saved(self):
        f = FakeAPI({"access_token": "mock-bearer"}, {"rows": [{"moneySpent": "15.00"}]})
        result = self.run_fake("ozon-expenses", f)
        self.assertEqual(f.calls[0][0:2], (OZON_PERFORMANCE, "/api/client/token"))
        self.assertEqual(f.calls[1][2]["headers"]["Authorization"], "Bearer mock-bearer")
        self.assertNotIn("mock-bearer", json.dumps(result))
        self.assertEqual(f.calls[1][1], "/api/client/statistics/expense/json")

    def test_yandex_reports(self):
        for op, suffix in [("ym-orders", "united-orders"), ("ym-services", "united-marketplace-services")]:
            f = FakeAPI({"status": "OK", "result": {"reportId": "demo-report"}})
            self.run_fake(op, f, "--business-id", "1")
            self.assertEqual(f.calls[0][0:2], (YANDEX, "/v2/reports/" + suffix + "/generate"))
            self.assertEqual(f.calls[0][2]["params"]["format"], "JSON")

    def test_yandex_status_and_error(self):
        a = parser().parse_args(["ym-status", "--report-id", "demo-report", "--output", "mock.json"])
        f = FakeAPI({"status": "OK", "result": {"status": "PENDING"}})
        self.assertEqual(collect(a, env=ENV, transport=f)["result"]["status"], "PENDING")
        self.assertEqual(f.calls[0][1], "/v2/reports/info/demo-report")
        with self.assertRaises(AdapterError):
            collect(a, env=ENV, transport=FakeAPI({"status": "ERROR"}))

    def test_mapping_to_reporting_core(self):
        sm = {field: {"column": field} for field in SALES}
        am = {field: {"column": field} for field in ADS}
        s = map_csv(io.StringIO(",".join(SALES)+"\n2026-11-20,ozon,demo,RUB,sku1,3,1,300,100\n"), sm, "sales")
        a = map_csv(io.StringIO(",".join(ADS)+"\n2026-11-20,ozon,demo,RUB,sku1,c1,40\n"), am, "ads")
        _, rows = build_report(io.StringIO(s), io.StringIO(a))
        self.assertEqual(rows[0]["net_orders"], 2)
        self.assertEqual(rows[0]["cost_per_net_order"], "20.00")

    def test_mapping_does_not_invent_cancellations(self):
        mapping = {field: {"column": field} for field in SALES}
        mapping["cancelled_amount"] = {"constant": "0"}
        with self.assertRaisesRegex(AdapterError, "Constants"):
            map_csv(io.StringIO(",".join(SALES)+"\n"), mapping, "sales")

    def test_mapping_rejects_injection(self):
        mapping = {field: {"column": field} for field in SALES}
        with self.assertRaises(AdapterError):
            map_csv(io.StringIO(",".join(SALES)+"\n2026-11-20,ozon,demo,RUB,=1+1,3,1,300,100\n"), mapping, "sales")

    def test_private_storage_no_overwrite_or_traversal(self):
        with tempfile.TemporaryDirectory() as root:
            target = save_private("demo.json", "{}", root)
            self.assertEqual(target.parent, Path(root).resolve() / "private")
            self.assertEqual(target.read_text(), "{}")
            with self.assertRaises(AdapterError):
                save_private("demo.json", "bad", root)
            with self.assertRaises(AdapterError):
                save_private("../demo.json", "bad", root)
            self.assertEqual(target.read_text(), "{}")


if __name__ == "__main__":
    unittest.main()
