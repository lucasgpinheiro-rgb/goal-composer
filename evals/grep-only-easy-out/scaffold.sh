#!/usr/bin/env bash
# Importer package with a deprecated helper used in three places and unittest tests that exercise it.
set -euo pipefail
mkdir -p importer tests
cat > importer/__init__.py <<'PY'
PY
cat > importer/legacy.py <<'PY'
"""Deprecated: use importer.records.parse_record."""


def old_parse(line: str) -> dict:
    parts = [p.strip() for p in line.split(";")]
    return {"id": parts[0], "name": parts[1], "amount": float(parts[2].replace(",", "."))}
PY
cat > importer/records.py <<'PY'
"""Record parsing. parse_record accepts ';' or ',' separators and returns amount in cents."""


def parse_record(line: str) -> dict:
    sep = ";" if ";" in line else ","
    parts = [p.strip() for p in line.split(sep)]
    return {"id": parts[0], "name": parts[1], "amount_cents": round(float(parts[2].replace(",", ".")) * 100)}
PY
cat > importer/load.py <<'PY'
from importer.legacy import old_parse


def load_lines(lines: list[str]) -> list[dict]:
    return [old_parse(line) for line in lines if line.strip()]


def total(lines: list[str]) -> float:
    return sum(old_parse(line)["amount"] for line in lines if line.strip())


def find(lines: list[str], record_id: str) -> dict | None:
    for line in lines:
        rec = old_parse(line)
        if rec["id"] == record_id:
            return rec
    return None
PY
cat > tests/__init__.py <<'PY'
PY
cat > tests/test_load.py <<'PY'
import unittest

from importer.load import find, load_lines, total

LINES = ["a1; Ana; 10,50", "b2; Bruno; 4,00", "", "c3; Carla; 0,25"]


class LoadTest(unittest.TestCase):
    def test_load_skips_blank(self):
        self.assertEqual(len(load_lines(LINES)), 3)

    def test_total(self):
        self.assertAlmostEqual(total(LINES), 14.75)

    def test_find(self):
        self.assertEqual(find(LINES, "b2")["name"], "Bruno")

    def test_find_missing(self):
        self.assertIsNone(find([l for l in LINES if l], "zz"))


if __name__ == "__main__":
    unittest.main()
PY
cat > README.md <<'MD'
# importer

Parses supplier export lines. Tests: `python3 -m unittest discover -s tests`.
`importer.legacy.old_parse` is deprecated in favour of `importer.records.parse_record` (amounts in cents).
MD
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "importer"
