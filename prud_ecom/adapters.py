# SPDX-License-Identifier: AGPL-3.0-only
"""Experimental read-only API collectors and explicit CSV column mapping.

No production account is bundled. The raw collectors do not certify complete
coverage or translate unlike marketplace metrics into net-order metrics.
"""
import argparse
import csv
import io
import json
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import Request, HTTPRedirectHandler, ProxyHandler, build_opener

from .report import SALES, ADS, DataError

WB_ANALYTICS = "https://seller-analytics-api.wildberries.ru"
WB_ADS = "https://advert-api.wildberries.ru"
OZON_SELLER = "https://api-seller.ozon.ru"
OZON_PERFORMANCE = "https://api-performance.ozon.ru"
YANDEX = "https://api.partner.market.yandex.ru"
MAX_RESPONSE = 32 * 1024 * 1024


class AdapterError(ValueError):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request_json(base, path, *, method="GET", headers=None, params=None, body=None):
    """Only fixed API origins; no redirects, proxy discovery or response-body logs."""
    if base not in (WB_ANALYTICS, WB_ADS, OZON_SELLER, OZON_PERFORMANCE, YANDEX):
        raise AdapterError("API host not allowed")
    if not path.startswith("/") or path.startswith("//") or "?" in path or "#" in path:
        raise AdapterError("Invalid API path")
    url = base + path + ("?" + urlencode(params, doseq=True) if params else "")
    all_headers = {"Accept": "application/json", "User-Agent": "PRUD-AI-e-com-daily/0.2.0"}
    if headers:
        all_headers.update(headers)
    payload = None
    if body is not None:
        all_headers["Content-Type"] = "application/json"
        payload = json.dumps(body).encode("utf-8")
    try:
        req = Request(url, data=payload, headers=all_headers, method=method)
        with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=30) as response:
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise AdapterError("Response too large; reduce request scope")
        result = json.loads(raw)
        if not isinstance(result, (list, dict)):
            raise AdapterError("Unexpected JSON response")
        return result
    except HTTPError as exc:
        message = "HTTP " + str(exc.code)
        if exc.code in (429, 420):
            message += ": rate limited; consult provider limits before retrying"
        if exc.code in (401, 403):
            message += ": check credential and subscription permissions"
        raise AdapterError(message) from None
    except (URLError, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        if isinstance(exc, AdapterError):
            raise
        raise AdapterError("API request failed or returned non-JSON data") from None


def secret(name, env):
    value = env.get(name, "").strip()
    if not value or any(ord(c) < 32 or ord(c) > 126 for c in value):
        raise AdapterError("Missing or invalid environment variable: " + name)
    return value


def period(start, end, max_days):
    if not start or not end or start > end or (end - start).days + 1 > max_days:
        raise AdapterError("Invalid date interval; maximum " + str(max_days) + " inclusive days")
    return start.isoformat(), end.isoformat()


def ids(values, maximum):
    if not values or len(values) > maximum or len(set(values)) != len(values) or any(v <= 0 for v in values):
        raise AdapterError("Provide unique positive IDs, at most " + str(maximum))
    return values


def object_result(value, name):
    if not isinstance(value, dict) or value.get("status") == "ERROR" or value.get("error") or value.get("errors"):
        raise AdapterError(name + ": provider returned an error or unexpected object")
    return value


def array_result(value, name):
    if not isinstance(value, list) or any(not isinstance(row, dict) for row in value):
        raise AdapterError(name + ": unexpected result; expected array of objects")
    return value


def collect(args, *, env=None, transport=None):
    """Execute a single bounded collection operation (two requests for Ozon ads)."""
    env = os.environ if env is None else env
    call = request_json if transport is None else transport
    op = args.operation
    if op == "wb-sales":
        start, end = period(args.start, args.end, 7)
        products = ids(args.ids, 20)
        return array_result(call(WB_ANALYTICS, "/api/analytics/v3/sales-funnel/products/history",
            method="POST", headers={"Authorization": secret("WB_ANALYTICS_TOKEN", env)},
            body={"selectedPeriod": {"start": start, "end": end}, "nmIds": products,
                  "skipDeletedNm": False, "aggregationLevel": "day"}), op)
    if op == "wb-expenses":
        start, end = period(args.start, args.end, 31)
        return array_result(call(WB_ADS, "/adv/v1/upd",
            headers={"Authorization": secret("WB_ADS_TOKEN", env)},
            params={"from": start, "to": end}), op)
    if op == "wb-ad-stats":
        start, end = period(args.start, args.end, 31)
        campaigns = ids(args.ids, 50)
        return array_result(call(WB_ADS, "/adv/v3/fullstats",
            headers={"Authorization": secret("WB_ADS_TOKEN", env)},
            params={"ids": ",".join(map(str, campaigns)), "beginDate": start, "endDate": end}), op)
    if op == "ozon-sales":
        start, end = period(args.start, args.end, 31)
        if not 1 <= args.limit <= 1000 or args.offset < 0:
            raise AdapterError("Invalid page limit or offset")
        metrics = ["ordered_units", "revenue"] + (["cancellations", "returns"] if args.extra_metrics else [])
        payload = object_result(call(OZON_SELLER, "/v1/analytics/data", method="POST",
            headers={"Client-Id": secret("OZON_CLIENT_ID", env), "Api-Key": secret("OZON_API_KEY", env)},
            body={"date_from": start, "date_to": end, "dimension": ["sku", "day"],
                  "metrics": metrics, "filters": [], "sort": [{"key": "ordered_units", "order": "DESC"}],
                  "limit": args.limit, "offset": args.offset}), op)
        result = object_result(payload.get("result"), op)
        rows = array_result(result.get("data"), op)
        for row in rows:
            if not isinstance(row.get("dimensions"), list) or len(row["dimensions"]) != 2:
                raise AdapterError("Unexpected Ozon dimensions")
            if not isinstance(row.get("metrics"), list) or len(row["metrics"]) != len(metrics):
                raise AdapterError("Unexpected Ozon metric count")
        return {"metric_order": metrics, "dimension_order": ["sku", "day"], "offset": args.offset,
                "limit": args.limit, "next_offset_candidate": args.offset + len(rows) if len(rows) == args.limit else None,
                "coverage_verified": False, "response": payload}
    if op == "ozon-expenses":
        start, end = period(args.start, args.end, 31)
        auth = object_result(call(OZON_PERFORMANCE, "/api/client/token", method="POST",
            body={"client_id": secret("OZON_PERFORMANCE_CLIENT_ID", env),
                  "client_secret": secret("OZON_PERFORMANCE_CLIENT_SECRET", env),
                  "grant_type": "client_credentials"}), op)
        token = secret("access_token", auth) if isinstance(auth.get("access_token"), str) else None
        if not token:
            raise AdapterError("Ozon Performance token missing")
        payload = call(OZON_PERFORMANCE, "/api/client/statistics/expense/json",
                       headers={"Authorization": "Bearer " + token},
                       params={"dateFrom": start, "dateTo": end})
        if isinstance(payload, dict):
            return object_result(payload, op)
        return array_result(payload, op)
    if op.startswith("ym-"):
        headers = {"Api-Key": secret("YANDEX_MARKET_TOKEN", env)}
        if op == "ym-status":
            rid = args.report_id
            if not rid or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,255}", rid) or rid in (".", ".."):
                raise AdapterError("Invalid report identifier")
            payload = call(YANDEX, "/v2/reports/info/" + quote(rid, safe=""), headers=headers)
        elif op in ("ym-orders", "ym-services"):
            start, end = period(args.start, args.end, 31)
            if not args.business_id or args.business_id <= 0:
                raise AdapterError("A positive business ID is required")
            report = {"ym-orders": "united-orders", "ym-services": "united-marketplace-services"}[op]
            payload = call(YANDEX, "/v2/reports/" + report + "/generate",
                method="POST", headers=headers, params={"format": "JSON", "language": "EN"},
                body={"businessId": args.business_id, "dateFrom": start, "dateTo": end})
        else:
            raise AdapterError("Unknown Market operation")
        result = object_result(payload, op)
        object_result(result.get("result"), op)
        if result.get("status") != "OK":
            raise AdapterError("Unexpected Market response status")
        return result
    raise AdapterError("Unknown collection operation")


def map_csv(source, mapping, kind):
    """Map already-aggregated source columns; never infer currency, spend or cancellations.

    A mapping entry is {"column": "source heading"} or {"constant": "value"}.
    Constants are restricted to marketplace, account, currency and date.
    Monetary and count metrics must come from actual source columns.
    """
    if kind not in ("sales", "ads"):
        raise AdapterError("Unknown mapping kind")
    fields = SALES if kind == "sales" else ADS
    if not isinstance(mapping, dict) or set(mapping) != set(fields):
        raise AdapterError("Mapping must contain exactly the normalized fields")
    reader = csv.DictReader(source)
    names = reader.fieldnames or []
    if not names or len(names) != len(set(names)):
        raise AdapterError("Missing or duplicated source headings")
    for field, spec in mapping.items():
        if not isinstance(spec, dict) or len(spec) != 1:
            raise AdapterError("Invalid mapping rule: " + field)
        if "column" in spec:
            if spec["column"] not in names:
                raise AdapterError("Missing source column: " + field)
        elif "constant" in spec:
            if field not in ("marketplace", "account", "currency", "date") or not isinstance(spec["constant"], str):
                raise AdapterError("Constants are only allowed for metadata")
        else:
            raise AdapterError("Invalid mapping rule")
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    count = 0
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise AdapterError("Malformed input CSV row")
        mapped = {field: str(spec["constant"] if "constant" in spec else row[spec["column"]]).strip()
                  for field, spec in mapping.items()}
        if any(not v or v.startswith(("=", "+", "-", "@")) or any(ord(c) < 32 for c in v) for v in mapped.values()):
            raise AdapterError("Empty, negative or unsafe mapped field")
        writer.writerow(mapped)
        count += 1
    if not count:
        raise AdapterError("No source rows; absence is not zero")
    return output.getvalue()


def save_private(filename, content, root=None):
    """Store only in the ignored private directory; refuse overwrite or symlink escape."""
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,100}\.(json|csv)", filename):
        raise AdapterError("Use a simple .json or .csv filename (no directory path)")
    root = (Path.cwd() if root is None else Path(root)).resolve()
    folder = root / "private"
    if folder.is_symlink():
        raise AdapterError("Private output directory must not be a symlink")
    folder.mkdir(mode=0o700, exist_ok=True)
    target = folder / filename
    try:
        fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        raise AdapterError("Output already exists; choose another filename") from None
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
            stream.write(content)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


def parser():
    p = argparse.ArgumentParser(description="PRUD AI e-com daily — experimental marketplace adapters")
    sub = p.add_subparsers(dest="operation", required=True)
    operations = ("wb-sales", "wb-expenses", "wb-ad-stats", "ozon-sales", "ozon-expenses",
                  "ym-orders", "ym-services", "ym-status")
    for op in operations:
        s = sub.add_parser(op)
        s.add_argument("--output", required=True, help="New JSON filename in private/")
        if op != "ym-status":
            s.add_argument("--start", required=True, type=date.fromisoformat)
            s.add_argument("--end", required=True, type=date.fromisoformat)
        if op in ("wb-sales", "wb-ad-stats"):
            s.add_argument("--ids", type=int, nargs="+", required=True)
        if op == "ozon-sales":
            s.add_argument("--limit", type=int, default=1000)
            s.add_argument("--offset", type=int, default=0)
            s.add_argument("--extra-metrics", action="store_true")
        if op in ("ym-orders", "ym-services"):
            s.add_argument("--business-id", type=int, required=True)
        if op == "ym-status":
            s.add_argument("--report-id", required=True)
    s = sub.add_parser("map-csv")
    s.add_argument("--kind", choices=("sales", "ads"), required=True)
    s.add_argument("--input", type=Path, required=True)
    s.add_argument("--mapping", type=Path, required=True)
    s.add_argument("--output", required=True, help="New CSV filename in private/")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.operation == "map-csv":
            if not args.output.endswith(".csv"):
                raise AdapterError("Mapping output must have .csv extension")
            with args.mapping.open(encoding="utf-8-sig") as m, args.input.open(encoding="utf-8-sig", newline="") as src:
                content = map_csv(src, json.load(m), args.kind)
        else:
            if not args.output.endswith(".json"):
                raise AdapterError("Collector output must have .json extension")
            raw = collect(args)
            content = json.dumps({"operation": args.operation,
                                  "collected_at_utc": datetime.now(timezone.utc).isoformat(),
                                  "start": args.start.isoformat() if getattr(args, "start", None) else None,
                                  "end": args.end.isoformat() if getattr(args, "end", None) else None,
                                  "coverage_verified": False, "data": raw}, ensure_ascii=False, indent=2)
        target = save_private(args.output, content)
        print("Saved locally:", target.name, "in private/. Verify source coverage and metric definitions.")
        return 0
    except (AdapterError, DataError) as exc:
        print("Adapter stopped:", exc, file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, csv.Error):
        print("Adapter stopped: invalid local input or output", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
