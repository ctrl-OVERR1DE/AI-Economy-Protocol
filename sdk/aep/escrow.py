"""Escrow helpers (placeholder).

This module is a placeholder for Solana escrow helpers. In this MVP SDK, escrow
is managed by the Marketplace API and on-chain programs. A future version will
expose convenience methods for:

- Creating/loading associated token accounts
- Initializing escrow accounts
- Submitting and verifying proofs
- Parsing on-chain receipts

For now, use the MarketplaceClient for API interactions and PaymentClient for
payment release via x402.
"""

from __future__ import annotations


def not_implemented(*_args, **_kwargs):  # pragma: no cover
    raise NotImplementedError("Escrow helpers are not implemented in the MVP SDK.")
