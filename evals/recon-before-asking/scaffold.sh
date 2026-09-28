#!/usr/bin/env bash
# CLI with a `report` command that prints a text table; unittest tests; no CSV support yet.
set -euo pipefail
mkdir -p reports tests
cat > reports/__init__.py <<'PY'
PY
cat > reports/data.py <<'PY'
SALES = [
    {"region": "North", "month": "2026-07", "orders": 120, "revenue_cents": 1845000},
    {"region": "South", "month": "2026-07", "orders": 98, "revenue_cents": 1520050},
    {"region": "North", "month": "2026-08", "orders": 131, "revenue_cents": 2010000},
]
PY
cat > reports/cli.py <<'PY'
"""Command line entry point: python3 -m reports.cli report [--region NAME]."""
import argparse
import sys

from reports.data import SALES


def render_table(rows: list[dict]) -> str:
    lines = [f"{'region':<8}{'month':<9}{'orders':>7}{'revenue':>12}"]
    for r in rows:
        lines.append(f"{r['region']:<8}{r['month']:<9}{r['orders']:>7}{r['revenue_cents'] / 100:>12.2f}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reports")
    sub = parser.add_subparsers(dest="command", required=True)
    rep = sub.add_parser("report", help="print the sales report")
    rep.add_argument("--region")
    args = parser.parse_args(argv)
    rows = [r for r in SALES if not args.region or r["region"] == args.region]
    print(render_table(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
PY
cat > tests/__init__.py <<'PY'
PY
cat > tests/test_cli.py <<'PY'
import contextlib
import io
import unittest

from reports.cli import main, render_table
from reports.data import SALES


class CliTest(unittest.TestCase):
    def run_cli(self, *argv):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(list(argv))
        return code, buf.getvalue()

    def test_report_all(self):
        code, out = self.run_cli("report")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 4)

    def test_report_region(self):
        _, out = self.run_cli("report", "--region", "South")
        self.assertIn("South", out)
        self.assertNotIn("North", out)

    def test_table_header(self):
        self.assertTrue(render_table(SALES).startswith("region"))


if __name__ == "__main__":
    unittest.main()
PY
cat > README.md <<'MD'
# reports

`python3 -m reports.cli report [--region NAME]` prints the monthly sales table.
Tests: `python3 -m unittest discover -s tests`.
MD
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "reports cli"
