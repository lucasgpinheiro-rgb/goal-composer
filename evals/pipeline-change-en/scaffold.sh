#!/usr/bin/env bash
# Billing client without retry, stdlib unittest suite (no third-party packages needed), clean git tree.
set -euo pipefail
mkdir -p billing tests
cat > billing/__init__.py <<'PY'
PY
cat > billing/client.py <<'PY'
"""HTTP client for the billing service."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class TransportTimeout(Exception):
    """The request did not complete in time."""


class HTTPError(Exception):
    def __init__(self, status: int, body: str = "") -> None:
        super().__init__(f"HTTP {status}")
        self.status = status
        self.body = body


class Transport(Protocol):
    def get(self, url: str, timeout: float) -> dict[str, Any]: ...


@dataclass
class Invoice:
    id: str
    customer_id: str
    amount_cents: int
    currency: str
    status: str

    @classmethod
    def from_json(cls, data: dict[str, Any]) -> "Invoice":
        return cls(
            id=str(data["id"]),
            customer_id=str(data["customer_id"]),
            amount_cents=int(data["amount_cents"]),
            currency=str(data.get("currency", "BRL")),
            status=str(data["status"]),
        )


class BillingClient:
    def __init__(self, transport: Transport, base_url: str, timeout: float = 5.0) -> None:
        self.transport = transport
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def invoice_url(self, invoice_id: str) -> str:
        if not invoice_id:
            raise ValueError("invoice_id is required")
        return f"{self.base_url}/invoices/{invoice_id}"

    def fetch_invoice(self, invoice_id: str) -> Invoice:
        data = self.transport.get(self.invoice_url(invoice_id), timeout=self.timeout)
        return Invoice.from_json(data)
PY
cat > tests/__init__.py <<'PY'
PY
cat > tests/test_client.py <<'PY'
import unittest
from typing import Any

from billing.client import BillingClient, HTTPError, Invoice, TransportTimeout

PAYLOAD = {"id": "inv_1", "customer_id": "c_9", "amount_cents": 12900, "currency": "BRL", "status": "open"}


class FakeTransport:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls: list[str] = []

    def get(self, url: str, timeout: float) -> dict[str, Any]:
        self.calls.append(url)
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


class ClientTest(unittest.TestCase):
    def test_parses_payload(self):
        inv = BillingClient(FakeTransport([PAYLOAD]), "https://api.example.com").fetch_invoice("inv_1")
        self.assertEqual(inv, Invoice("inv_1", "c_9", 12900, "BRL", "open"))

    def test_builds_url(self):
        t = FakeTransport([PAYLOAD])
        BillingClient(t, "https://api.example.com/").fetch_invoice("inv_1")
        self.assertEqual(t.calls, ["https://api.example.com/invoices/inv_1"])

    def test_empty_id_rejected(self):
        with self.assertRaises(ValueError):
            BillingClient(FakeTransport([]), "https://x").fetch_invoice("")

    def test_currency_default(self):
        payload = {k: v for k, v in PAYLOAD.items() if k != "currency"}
        self.assertEqual(Invoice.from_json(payload).currency, "BRL")

    def test_amount_is_int(self):
        self.assertEqual(Invoice.from_json({**PAYLOAD, "amount_cents": "999"}).amount_cents, 999)

    def test_status_passthrough(self):
        self.assertEqual(Invoice.from_json({**PAYLOAD, "status": "void"}).status, "void")

    def test_default_timeout(self):
        self.assertEqual(BillingClient(FakeTransport([]), "https://x").timeout, 5.0)

    def test_http_error_status(self):
        err = HTTPError(503, "boom")
        self.assertEqual((err.status, str(err)), (503, "HTTP 503"))

    def test_timeout_is_exception(self):
        self.assertTrue(issubclass(TransportTimeout, Exception))


if __name__ == "__main__":
    unittest.main()
PY
cat > README.md <<'MD'
# acme-billing

Client for the billing service. Tests: `python3 -m unittest discover -s tests -v`.
MD
printf '__pycache__/\n' > .gitignore
git init -q && git add -A && git -c user.name=eval -c user.email=eval@example.com commit -qm "billing client"
