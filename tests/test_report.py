# SPDX-License-Identifier: AGPL-3.0-only
import csv
import io
import unittest
from datetime import date
from pathlib import Path
from prud_ecom.report import DataError, build_report, csv_report, SALES, ADS

ROOT = Path(__file__).resolve().parents[1]
K = '2026-11-20,wildberries,demo,RUB,sku'

def data(s=None, a=None, **kwargs):
    return build_report(io.StringIO(','.join(SALES)+'\n'+(s if s is not None else K+',10,2,1000,200\n')),
                        io.StringIO(','.join(ADS)+'\n'+(a if a is not None else K+',c1,40\n'+K+',c2,60\n')), **kwargs)[1]

class TestReport(unittest.TestCase):
    def test_campaign_sum_and_net_metrics(self):
        r = data()[0]
        self.assertEqual(r['net_orders'], 8)
        self.assertEqual(r['net_ordered_amount'], '800.00')
        self.assertEqual(r['ad_spend'], '100.00')
        self.assertEqual(r['cost_per_net_order'], '12.50')
        self.assertEqual(r['ad_spend_pct_net_amount'], '12.50')

    def test_zero_denominator_preserves_spend(self):
        r = data(s=K+',0,0,0,0\n')[0]
        self.assertEqual(r['ad_spend'], '100.00')
        self.assertEqual(r['cost_per_net_order'], '')
        self.assertEqual(r['ad_spend_pct_net_amount'], '')

    def test_explicit_zero_ads(self):
        self.assertEqual(data(a=K+',no_ads,0\n')[0]['ad_spend_pct_net_amount'], '0.00')

    def test_duplicate_sales(self):
        with self.assertRaisesRegex(DataError, 'duplicate sales'):
            data(s=(K+',10,2,1000,200\n')*2)

    def test_duplicate_campaign(self):
        with self.assertRaisesRegex(DataError, 'duplicate campaign'):
            data(a=(K+',c1,40\n')*2)

    def test_missing_ads(self):
        with self.assertRaisesRegex(DataError, 'missing ads'):
            data(a='')

    def test_missing_sales(self):
        with self.assertRaisesRegex(DataError, 'missing sales'):
            data(s='')

    def test_excess_cancellations(self):
        with self.assertRaisesRegex(DataError, 'cancellations exceed'):
            data(s=K+',2,3,1000,200\n')

    def test_invalid_values(self):
        for val in ['NaN','-1','1.001','Infinity']:
            with self.subTest(val=val), self.assertRaises(DataError):
                data(a=K+',c1,'+val+'\n')

    def test_spreadsheet_formula_identifier(self):
        with self.assertRaisesRegex(DataError, 'unsafe spreadsheet identifier'):
            data(s=K.replace(',sku', ',=1+1')+',10,2,1000,200\n')

    def test_empty_value(self):
        with self.assertRaises(DataError):
            data(a=K+',c1,\n')

    def test_date_range(self):
        with self.assertRaisesRegex(DataError, 'no data'):
            data(start=date(2026,11,21))

    def test_period_weighting_and_currency_separation(self):
        _, results = csv_report(ROOT/'examples/sales.csv', ROOT/'examples/ads.csv', group='period')
        self.assertEqual(len(results), 4)
        wb = next(x for x in results if x['marketplace']=='wildberries')
        self.assertEqual(wb['net_orders'], 16)
        self.assertEqual(wb['ad_spend'], '1700.00')
        self.assertEqual(wb['cost_per_net_order'], '106.25')
        self.assertEqual(wb['ad_spend_pct_net_amount'], '10.63')
        am = next(x for x in results if x['marketplace']=='amazon')
        self.assertEqual(am['currency'],'USD')
        self.assertEqual(am['ad_spend'],'5.00')

if __name__ == '__main__':
    unittest.main()
