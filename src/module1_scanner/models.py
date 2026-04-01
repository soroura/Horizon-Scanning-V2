"""
ScanItem — pydantic v2 model for a single normalised item from Module 1.
Constitution Principle III: this is the sole contract between Module 1 and Module 2.
"""
from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone

from pydantic import BaseModel, field_validator, model_validator


class ScanItem(BaseModel):
    # ── Identity ──────────────────────────────────────────────────────────────
    id: str                          # SHA-256 hex of (source_id + url)
    source_id: str
    source_name: str
    category: str
    horizon_tier: str                # H1 | H2 | H3 | H4

    # ── Content ───────────────────────────────────────────────────────────────
    title: str
    url: str
    summary: str                     # abstract / first 500 chars
    full_text: str | None = None

    # ── Metadata ──────────────────────────────────────────────────────────────
    published_date: date
    retrieved_date: date
    authors: list[str] = []
    journal: str | None = None
    doi: str | None = None
    pmid: str | None = None

    # ── Domain tagging ────────────────────────────────────────────────────────
    domains: list[str] = []
    keywords_matched: list[str] = []

    # ── Access ────────────────────────────────────────────────────────────────
    access_model: str = "free"       # free | subscription | registration
    is_preprint: bool = False

    # ── Validators ────────────────────────────────────────────────────────────
    @field_validator("id")
    @classmethod
    def id_is_sha256(cls, v: str) -> str:
        if len(v) != 64 or not all(c in "0123456789abcdef" for c in v):
            raise ValueError(f"id must be a 64-char hex SHA-256, got: '{v[:20]}...'")
        return v

    @field_validator("url")
    @classmethod
    def url_is_https(cls, v: str) -> str:
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f"url must be http(s), got: '{v}'")
        return v

    @field_validator("published_date")
    @classmethod
    def date_not_future(cls, v: date) -> date:
        today = date.today()  # local date — avoids UTC/local timezone edge cases
        if v > today:
            raise ValueError(f"published_date cannot be in the future: {v}")
        return v

    @field_validator("horizon_tier")
    @classmethod
    def valid_horizon_tier(cls, v: str) -> str:
        if v not in {"H1", "H2", "H3", "H4"}:
            raise ValueError(f"horizon_tier must be H1–H4, got: '{v}'")
        return v

    # ── Convenience constructor ───────────────────────────────────────────────
    @classmethod
    def make_id(cls, source_id: str, url: str) -> str:
        """Deterministic SHA-256 id from source_id + url."""
        raw = (source_id + url).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
