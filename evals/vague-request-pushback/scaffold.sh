#!/usr/bin/env bash
# Small Python search service with a benchmark script and stdlib unittest tests.
set -euo pipefail
mkdir -p app tests scripts
cat > app/__init__.py <<'PY'
PY
cat > app/search.py <<'PY'
"""Naive full-text search over an in-memory list of documents."""


def tokenize(text: str) -> list[str]:
    return [t.strip(".,;:!?").lower() for t in text.split() if t.strip(".,;:!?")]


def search(docs: list[str], query: str, limit: int = 10) -> list[int]:
    terms = tokenize(query)
    scored = []
    for i, doc in enumerate(docs):
        words = tokenize(doc)
        score = sum(words.count(t) for t in terms)
        if score:
            scored.append((-score, i))
    scored.sort()
    return [i for _, i in scored[:limit]]
PY
cat > app/ingest.py <<'PY'
"""Loads documents from a folder of .txt files."""
import pathlib


def load(folder: str) -> list[str]:
    return [p.read_text(encoding="utf-8") for p in sorted(pathlib.Path(folder).glob("*.txt"))]
PY
cat > tests/__init__.py <<'PY'
PY
cat > tests/test_search.py <<'PY'
import unittest

from app.search import search, tokenize


class SearchTest(unittest.TestCase):
    def test_tokenize(self):
        self.assertEqual(tokenize("Hello, World!"), ["hello", "world"])

    def test_ranks_by_count(self):
        docs = ["apple pie", "apple apple tart", "pear"]
        self.assertEqual(search(docs, "apple"), [1, 0])

    def test_limit(self):
        docs = ["x"] * 20
        self.assertEqual(len(search(docs, "x", limit=5)), 5)

    def test_no_match(self):
        self.assertEqual(search(["a b c"], "zzz"), [])


if __name__ == "__main__":
    unittest.main()
PY
cat > scripts/bench.py <<'PY'
"""Benchmark: p95 latency of search() over a synthetic corpus, printed as p95_ms=<n>."""
import random
import statistics
import sys
import time

sys.path.insert(0, ".")
from app.search import search  # noqa: E402

random.seed(1)
WORDS = [f"w{i}" for i in range(500)]
DOCS = [" ".join(random.choices(WORDS, k=200)) for _ in range(2000)]
times = []
for _ in range(30):
    q = " ".join(random.choices(WORDS, k=3))
    t0 = time.perf_counter()
    search(DOCS, q)
    times.append((time.perf_counter() - t0) * 1000)
print(f"p95_ms={statistics.quantiles(times, n=20)[18]:.0f}")
PY
cat > README.md <<'MD'
# search-service

In-memory search used by the docs portal. Run the tests with `python3 -m unittest discover -s tests`
and the benchmark with `python3 scripts/bench.py`.
MD
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "search service"
