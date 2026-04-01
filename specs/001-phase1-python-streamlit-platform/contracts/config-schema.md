# Configuration Schema Contract

**Type**: YAML configuration files
**Location**: `config/` directory
**Date**: 2026-03-25

These files are the authoritative configuration for the platform. Changing
behaviour (adding sources, adjusting weights, defining scan profiles) MUST be
done by editing these files — never by modifying Python source code.

---

## `config/sources.yaml`

```yaml
sources:
  - id: <snake_case_str>          # REQUIRED — unique identifier
    name: <str>                   # REQUIRED — human-readable name
    category: <category_code>     # REQUIRED — see taxonomy below
    url: <https_url>              # REQUIRED — homepage URL
    feed_type: <api|rss|web_scrape|download>  # REQUIRED
    feed_url: <https_url>         # REQUIRED — URL used by adapter
    access: <free|free_registration|subscription>  # REQUIRED
    auth_required: <bool>         # REQUIRED
    update_frequency: <continuous|daily|weekly|monthly>  # REQUIRED
    domains:                      # REQUIRED — at least one
      - <domain_code>
    horizon_tier: <H1|H2|H3|H4>  # REQUIRED
    programmatic_access: <full|rss_only|download_only|manual>  # REQUIRED
    priority_rank: <int|null>     # OPTIONAL
    notes: <str>                  # OPTIONAL — free text
    active: <bool>                # REQUIRED
```

**Validation**: All REQUIRED fields must be present. `active: false` sources
are loaded but skipped during scan execution. Config validation errors print
the source `id` and missing field, then exit with code 1.

---

## `config/domains.yaml`

```yaml
domains:
  <domain_code>:
    name: <str>           # Human-readable domain name
    keywords:             # List of keyword strings (case-insensitive match)
      - <str>
      - <str>
    ...
```

**Example**:
```yaml
domains:
  ai_health:
    name: "AI in Health"
    keywords:
      - "clinical AI"
      - "machine learning in medicine"
      - "deep learning radiology"
      - "LLM healthcare"
      - "FDA AI"
      ...
  digital_health:
    name: "Digital Health"
    keywords:
      - "electronic health record"
      - "EHR"
      - "HL7 FHIR"
      - "telehealth"
      - "mHealth"
      ...
```

**Matching logic**: A keyword matches if it appears as a substring (case-
insensitive) in `title + " " + summary`. A ScanItem is tagged with all domains
whose keyword lists have at least one match. Items with no domain match are
dropped (not emitted to scorer).

---

## `config/scan_profiles.yaml`

```yaml
profiles:
  <profile_id>:
    name: <str>                          # Display name
    domains: <list[str]|["all"]>         # Domain filter
    days: <int>                          # Look-back window
    horizon_tiers: <list[H1|H2|H3|H4]>  # Tier filter
    categories: <list[str]|["all"]>      # Source category filter
```

**Built-in profiles** (must be present in the file):

| Profile ID | Description |
|-----------|-------------|
| `phase1_ai_digital` | Phase 1 — AI & Digital Health; H1–H3; 30 days |
| `full_scan` | All domains; H1–H4; 30 days |
| `safety_only` | Safety/regulatory; H1; 7 days |
| `insurance_focus` | All domains; H1–H3; 30 days (insurance weight boosted) |

---

## `config/score_weights.yaml`

```yaml
profiles:
  <profile_id>:
    w_a: <float>   # Evidence Strength weight
    w_b: <float>   # Clinical Impact weight
    w_c: <float>   # Insurance Readiness weight
    w_d: <float>   # Domain Relevance weight
```

**Constraint**: For each profile, `w_a + w_b + w_c + w_d` must equal `1.0`
(±0.001 floating-point tolerance). Validation failure exits with code 1.

**Built-in weight profiles**:

| Profile | w_a | w_b | w_c | w_d |
|---------|-----|-----|-----|-----|
| `phase1_ai_digital` | 0.25 | 0.30 | 0.20 | 0.25 |
| `full_scan` (clinical) | 0.30 | 0.35 | 0.25 | 0.10 |
| `safety_only` | 0.40 | 0.35 | 0.15 | 0.10 |
| `insurance_focus` | 0.20 | 0.25 | 0.45 | 0.10 |
