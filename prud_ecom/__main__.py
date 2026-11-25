# SPDX-License-Identifier: AGPL-3.0-only
"""Command-line entry point."""
import argparse
import csv
import os
import sys
import tempfile
from datetime import date
from pathlib import Path

from .report import DataError, csv_report


def main(argv=None):
    parser = argparse.ArgumentParser(description='PRUD AI e-com daily — local marketplace reports')
    parser.add_argument('--sales', type=Path, required=True, help='Normalized daily sales CSV')
    parser.add_argument('--ads', type=Path, required=True, help='Normalized daily campaign CSV')
    parser.add_argument('--group', choices=['sku', 'daily', 'period'], default='sku')
    parser.add_argument('--start', type=date.fromisoformat)
    parser.add_argument('--end', type=date.fromisoformat)
    parser.add_argument('--output', type=Path, required=True, help='Output CSV path (overwritten only on success)')
    args = parser.parse_args(argv)
    temp = None
    try:
        if args.output.resolve() in (args.sales.resolve(), args.ads.resolve()):
            raise DataError('output must not overwrite either input')
        fields, results = csv_report(args.sales, args.ads, group=args.group, start=args.start, end=args.end)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8-sig', newline='', dir=args.output.parent,
                                         delete=False, suffix='.tmp') as stream:
            temp = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(results)
        os.replace(temp, args.output)
        print(f'Wrote {len(results)} report rows to {args.output}')
        return 0
    except (DataError, OSError, UnicodeError, csv.Error) as exc:
        print(f'Report not generated: {exc}', file=sys.stderr)
        return 2
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)

if __name__ == '__main__':
    raise SystemExit(main())
