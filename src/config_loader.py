"""
Config loader — loads and validates all YAML configuration files.
Constitution Principle II: configuration changes never require code changes.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, field_validator, model_validator

# ─── Default config directory ────────────────────────────────────────────────

_HERE = Path(__file__).parent.parent  # version2/ root
_CONFIG_DIR = _HERE / "config"


# ─── Pydantic models for each config file ────────────────────────────────────

class Source(BaseModel):
    id: str
    name: str
    category: str
    url: str
    feed_type: Literal["api", "rss", "web_scrape", "download"]
    feed_url: str
    access: Literal["free", "free_registration", "subscription"]
    auth_required: bool
    update_frequency: str
    domains: list[str]
    horizon_tier: Literal["H1", "H2", "H3", "H4"]
    programmatic_access: str
    priority_rank: int | None = None
    notes: str = ""
    active: bool
    skip_domain_filter: bool = False  # if True, bypass keyword gate — emit all items

    @field_validator("id")
    @classmethod
    def id_snake_case(cls, v: str) -> str:
        import re
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(f"id must be snake_case, got: '{v}'")
        return v

    @field_validator("domains")
    @classmethod
    def domains_non_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("domains must contain at least one entry")
        return v


class ScanProfile(BaseModel):
    name: str
    domains: list[str]
    days: int
    horizon_tiers: list[str]
    categories: list[str]


class ScoreWeights(BaseModel):
    w_a: float
    w_b: float
    w_c: float
    w_d: float

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "ScoreWeights":
        total = self.w_a + self.w_b + self.w_c + self.w_d
        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Score weights must sum to 1.0, got {total:.4f} "
                f"(w_a={self.w_a}, w_b={self.w_b}, w_c={self.w_c}, w_d={self.w_d})"
            )
        return self


class DomainDefinition(BaseModel):
    name: str
    keywords: list[str]


# ─── Loader functions ─────────────────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        _config_error(f"Config file not found: {path}")
    except yaml.YAMLError as exc:
        _config_error(f"YAML parse error in {path}: {exc}")


def _config_error(msg: str) -> None:
    print(f"Config validation error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_sources(config_dir: Path = _CONFIG_DIR) -> list[Source]:
    """Load and validate all sources from sources.yaml."""
    data = _load_yaml(config_dir / "sources.yaml")
    sources = []
    for raw in data.get("sources", []):
        try:
            sources.append(Source.model_validate(raw))
        except Exception as exc:
            source_id = raw.get("id", "<unknown>")
            _config_error(f"Invalid source '{source_id}': {exc}")
    return sources


def load_active_sources(
    config_dir: Path = _CONFIG_DIR,
    domains: list[str] | None = None,
    categories: list[str] | None = None,
    horizon_tiers: list[str] | None = None,
) -> list[Source]:
    """Return active sources, optionally filtered by domains/categories/tiers."""
    all_sources = load_sources(config_dir)
    active = [s for s in all_sources if s.active]

    if domains and "all" not in domains:
        active = [s for s in active if any(d in domains for d in s.domains)]

    if categories and "all" not in categories:
        active = [s for s in active if s.category in categories]

    if horizon_tiers and "all" not in horizon_tiers:
        active = [s for s in active if s.horizon_tier in horizon_tiers]

    return active


def load_profiles(config_dir: Path = _CONFIG_DIR) -> dict[str, ScanProfile]:
    """Load and validate all scan profiles."""
    data = _load_yaml(config_dir / "scan_profiles.yaml")
    profiles = {}
    for pid, raw in data.get("profiles", {}).items():
        try:
            profiles[pid] = ScanProfile.model_validate(raw)
        except Exception as exc:
            _config_error(f"Invalid scan profile '{pid}': {exc}")
    return profiles


def load_profile(name: str, config_dir: Path = _CONFIG_DIR) -> ScanProfile:
    """Load a single named scan profile. Exits with error if not found."""
    profiles = load_profiles(config_dir)
    if name not in profiles:
        _config_error(
            f"Scan profile '{name}' not found. "
            f"Available: {', '.join(profiles.keys())}"
        )
    return profiles[name]


def load_weights(config_dir: Path = _CONFIG_DIR) -> dict[str, ScoreWeights]:
    """Load and validate all score weight profiles."""
    data = _load_yaml(config_dir / "score_weights.yaml")
    weights = {}
    for pid, raw in data.get("profiles", {}).items():
        try:
            weights[pid] = ScoreWeights.model_validate(raw)
        except Exception as exc:
            _config_error(f"Invalid score weights for profile '{pid}': {exc}")
    return weights


def load_profile_weights(profile_name: str, config_dir: Path = _CONFIG_DIR) -> ScoreWeights:
    """Load score weights for a specific profile."""
    weights = load_weights(config_dir)
    if profile_name not in weights:
        # Fall back to full_scan weights if profile-specific weights missing
        if "full_scan" in weights:
            return weights["full_scan"]
        _config_error(
            f"No score weights found for profile '{profile_name}' and no fallback available."
        )
    return weights[profile_name]


def load_domains(config_dir: Path = _CONFIG_DIR) -> dict[str, DomainDefinition]:
    """Load and validate all domain keyword banks."""
    data = _load_yaml(config_dir / "domains.yaml")
    domains = {}
    for domain_id, raw in data.get("domains", {}).items():
        try:
            domains[domain_id] = DomainDefinition.model_validate(raw)
        except Exception as exc:
            _config_error(f"Invalid domain definition '{domain_id}': {exc}")
    return domains
