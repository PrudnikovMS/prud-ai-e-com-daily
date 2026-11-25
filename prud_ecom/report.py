# SPDX-License-Identifier: AGPL-3.0-only
"""Deterministic reporting on normalized, complete daily marketplace data."""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import TextIO

KEY = ('date', 'marketplace', 'account', 'currency', 'sku')
SALES = KEY + ('orders', 'cancelled_orders', 'ordered_amount', 'cancelled_amount')
ADS = KEY + ('campaign_id', 'ad_spend')
METRICS = ('orders', 'cancelled_orders', 'net_orders', 'ordered_amount',
           'cancelled_amount', 'net_ordered_amount', 'ad_spend', 'cost_per_net_order', 'ad_spend_pct_net_amount')
ZERO = Decimal('0')

class DataError(ValueError):
    """Invalid or incomplete input; no partial report is emitted."""


def rows(stream: TextIO, required: tuple[str, ...], source: str):
    reader = csv.DictReader(stream)
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)) or set(fields) != set(required):
        raise DataError(f'{source}: expected exactly these columns: {", ".join(required)}')
    for row in reader:
        if None in row or any(v is None or not v.strip() for v in row.values()):
            raise DataError(f'{source} line {reader.line_num}: missing or extra field')
        yield reader.line_num, {k: v.strip() for k, v in row.items()}


def key_for(row, where):
    try:
        d = date.fromisoformat(row['date'])
        if d.isoformat() != row['date']:
            raise ValueError
    except ValueError as exc:
        raise DataError(f'{where}: date must be YYYY-MM-DD') from exc
    for field in ('marketplace', 'account', 'sku'):
        if row[field].startswith(('=', '+', '-', '@')) or any(ord(c) < 32 for c in row[field]):
            raise DataError(f'{where}: unsafe spreadsheet identifier in {field}; map to a safe ID')
    currency = row['currency'].upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise DataError(f'{where}: currency must be a three-letter code')
    return (d.isoformat(), row['marketplace'].lower(), row['account'], currency, row['sku'])


def number(value, where, *, integer=False):
    try:
        n = Decimal(value)
        if not n.is_finite() or n < 0 or (integer and n != n.to_integral_value()):
            raise ValueError
        if not integer and n != n.quantize(Decimal('0.01')):
            raise ValueError
        if n > Decimal('1000000000000000'):
            raise ValueError
        return int(n) if integer else n
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise DataError(f'{where}: expected a nonnegative {"integer" if integer else "amount (up to two decimals)"}') from exc


@dataclass
class Totals:
    orders: int = 0
    cancelled_orders: int = 0
    ordered_amount: Decimal = ZERO
    cancelled_amount: Decimal = ZERO
    ad_spend: Decimal = ZERO

    def add(self, other):
        self.orders += other.orders
        self.cancelled_orders += other.cancelled_orders
        self.ordered_amount += other.ordered_amount
        self.cancelled_amount += other.cancelled_amount
        self.ad_spend += other.ad_spend

    def result(self):
        net_orders = self.orders - self.cancelled_orders
        net_amount = self.ordered_amount - self.cancelled_amount
        def money(n):
            return format(n.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), 'f')
        return dict(orders=self.orders, cancelled_orders=self.cancelled_orders,
                    net_orders=net_orders, ordered_amount=money(self.ordered_amount),
                    cancelled_amount=money(self.cancelled_amount), net_ordered_amount=money(net_amount),
                    ad_spend=money(self.ad_spend),
                    cost_per_net_order=money(self.ad_spend / net_orders) if net_orders else '',
                    ad_spend_pct_net_amount=money(self.ad_spend * 100 / net_amount) if net_amount else '')


def build_report(sales: TextIO, ads: TextIO, *, group='sku', start=None, end=None):
    """Join sales and ad spending by date, marketplace, account, currency and SKU.

    Missing data is an error, not zero. An explicit zero row is required on either
    side when there were no sales or no ad spend. Multiple campaigns are summed.
    Net order metrics use cancellations attributed to the same order cohort.
    """
    if group not in ('sku', 'daily', 'period'):
        raise DataError('unknown grouping')
    if start and end and start > end:
        raise DataError('start date must not be after end date')
    def included(key):
        d = date.fromisoformat(key[0])
        return (start is None or d >= start) and (end is None or d <= end)
    sales_data = {}
    ad_data = defaultdict(lambda: ZERO)
    seen_campaigns = set()
    for line, row in rows(sales, SALES, 'sales'):
        loc = f'sales line {line}'
        k = key_for(row, loc)
        if not included(k):
            continue
        if k in sales_data:
            raise DataError(f'{loc}: duplicate sales key {k!r}')
        t = Totals(number(row['orders'], loc+' orders', integer=True),
                   number(row['cancelled_orders'], loc+' cancelled_orders', integer=True),
                   number(row['ordered_amount'], loc+' ordered_amount'),
                   number(row['cancelled_amount'], loc+' cancelled_amount'))
        if t.cancelled_orders > t.orders or t.cancelled_amount > t.ordered_amount:
            raise DataError(f'{loc}: cancellations exceed original orders or amount; check order cohort')
        sales_data[k] = t
    for line, row in rows(ads, ADS, 'ads'):
        loc = f'ads line {line}'
        k = key_for(row, loc)
        if not included(k):
            continue
        campaign = k + (row['campaign_id'],)
        if campaign in seen_campaigns:
            raise DataError(f'{loc}: duplicate campaign key {campaign!r}')
        seen_campaigns.add(campaign)
        ad_data[k] += number(row['ad_spend'], loc+' ad_spend')
    if not sales_data and not ad_data:
        raise DataError('no data for selected date range')
    missing_ads = sales_data.keys() - ad_data.keys()
    missing_sales = ad_data.keys() - sales_data.keys()
    if missing_ads or missing_sales:
        raise DataError(f'incomplete join: {len(missing_ads)} missing ads keys; {len(missing_sales)} missing sales keys. '
                        f'Examples: ads={sorted(missing_ads)[:3]!r}; sales={sorted(missing_sales)[:3]!r}')
    columns = {'sku': KEY, 'daily': KEY[:-1], 'period': KEY[1:-1]}[group]
    totals = defaultdict(Totals)
    for k, t in sales_data.items():
        t.ad_spend = ad_data[k]
        g = {'sku': k, 'daily': k[:-1], 'period': k[1:-1]}[group]
        totals[g].add(t)
    results = [dict(zip(columns, k)) | totals[k].result() for k in sorted(totals)]
    return columns + METRICS, results


def csv_report(sales_path: Path, ads_path: Path, **kwargs):
    with sales_path.open(encoding='utf-8-sig', newline='') as sales, ads_path.open(encoding='utf-8-sig', newline='') as ads:
        return build_report(sales, ads, **kwargs)
