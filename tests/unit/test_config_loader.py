"""Unit tests for config_loader — verifies YAML loading and pydantic validation."""
import pytest

from src.config_loader import (
    load_sources,
    load_active_sources,
    load_profiles,
    load_profile,
    load_weights,
    load_domains,
)


class TestLoadSources:
    def test_loads_all_sources(self):
        sources = load_sources()
        assert len(sources) >= 15  # at least 15 Phase 1 sources

    def test_each_source_has_required_fields(self):
        for s in load_sources():
            assert s.id, f"Source missing id"
            assert s.name, f"Source {s.id} missing name"
            assert s.feed_url, f"Source {s.id} missing feed_url"
            assert s.feed_type in ("rss", "api", "web_scrape", "download"), (
                f"Source {s.id} has invalid feed_type: {s.feed_type}"
            )
            assert s.horizon_tier in ("H1", "H2", "H3", "H4"), (
                f"Source {s.id} has invalid horizon_tier: {s.horizon_tier}"
            )

    def test_active_sources_subset(self):
        all_src = load_sources()
        active = load_active_sources()
        assert len(active) <= len(all_src)
        assert all(s.active for s in active)


class TestLoadProfiles:
    def test_loads_all_profiles(self):
        profiles = load_profiles()
        assert len(profiles) >= 4

    def test_phase1_profile_exists(self):
        profile = load_profile("phase1_ai_digital")
        assert "ai_health" in profile.domains

    def test_unknown_profile_raises(self):
        with pytest.raises(SystemExit):
            load_profile("nonexistent_profile")


class TestLoadWeights:
    def test_weights_sum_to_one(self):
        weights = load_weights()
        for profile_name, w in weights.items():
            total = w.w_a + w.w_b + w.w_c + w.w_d
            assert abs(total - 1.0) < 0.01, (
                f"Weights for {profile_name} sum to {total}, expected 1.0"
            )


class TestLoadDomains:
    def test_loads_domains(self):
        domains = load_domains()
        assert "ai_health" in domains
        assert "digital_health" in domains

    def test_domains_have_keywords(self):
        domains = load_domains()
        for name, domain in domains.items():
            assert len(domain.keywords) > 10, (
                f"Domain {name} has too few keywords: {len(domain.keywords)}"
            )
