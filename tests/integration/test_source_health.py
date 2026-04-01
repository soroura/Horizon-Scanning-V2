"""Integration test — source health tracking."""
import pytest
from src.module1_scanner.engine import SourceResult


class TestSourceResult:
    def test_ok_status(self):
        r = SourceResult("test", "Test", "ok", 10, "", 1200)
        assert r.status == "ok"
        assert r.items_count == 10

    def test_error_status(self):
        r = SourceResult("test", "Test", "error", 0, "timeout", 30000)
        assert r.status == "error"
        assert r.error_message == "timeout"

    def test_warn_status(self):
        r = SourceResult("test", "Test", "warn", 0, "", 500)
        assert r.status == "warn"
