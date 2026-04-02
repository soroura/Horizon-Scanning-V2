# R3.0 — Trend Intelligence Design Spec

**Date:** 2026-04-02
**Status:** Approved
**Goal:** Add cross-run analysis to detect new topics, track domain score trends, and identify coverage gaps.

## Problem

Each scan run is currently independent. There's no way to answer:
- "What's new this week that wasn't in last week's scan?"
- "Are ai_health items scoring higher or lower over time?"
- "Which source categories haven't produced anything recently?"

## Solution

Three new query functions in `trend.py`, surfaced in both the Markdown brief and a new dashboard tab. All queries work on existing SQLite data — no schema changes.

### 1. New Topics Detection

Query: items in the latest run whose `item_id` does not appear in any previous run.

```sql
SELECT si.* FROM scan_items si
WHERE si.run_id = :latest_run_id
AND si.item_id NOT IN (
    SELECT item_id FROM scan_items WHERE run_id != :latest_run_id
)
ORDER BY si.composite_score DESC
```

Returns a DataFrame of first-seen items. In the brief: "New This Period" section listing top 10 new items by score.

### 2. Domain Trends

Aggregate per domain per run: item count, mean composite score, count per triage level.

```sql
SELECT sr.run_id, sr.started_at, si.domains, si.composite_score, si.triage_level
FROM scan_items si
JOIN scan_runs sr ON si.run_id = sr.run_id
ORDER BY sr.started_at
```

Post-process in Python: explode JSON domains, group by (run_id, domain), compute count + mean score. Returns a DataFrame with columns: run_date, domain, item_count, avg_score.

In the dashboard: line chart (x=run date, y=item count, colour=domain).

### 3. Gap Analysis

Compare active source categories against latest run results:
- Load all active sources from config, group by category
- Load latest run items, group by category
- Categories with active sources but zero items = gap
- Domains present in previous runs but absent from latest = declining domain

Returns a dict: `{"category_gaps": [...], "domain_gaps": [...]}`.

### 4. Dashboard Trends Tab

New tab in Streamlit with:
- **Run History**: line chart of item count per run over time
- **New This Period**: table of first-seen items from latest run
- **Gap Alerts**: warning boxes for categories/domains with no activity

### 5. Cross-Source Dedup (R3.0-05)

Deferred. SHA-256(source_id + url) dedup is sufficient. Cross-source duplicates (same URL from different aggregators) are rare in practice.

## Files

| Action | File | Change |
|--------|------|--------|
| Modify | `src/module3_reporter/trend.py` | Add `get_new_topics_df()`, `get_domain_trends_df()`, `get_gap_analysis()` |
| Modify | `src/module3_reporter/templates/digest.md.j2` | Add "New This Period" and "Coverage Gaps" sections |
| Modify | `src/module3_reporter/formatters/markdown.py` | Pass trend data to template via run_meta |
| Modify | `app.py` | Add "Trends" tab |
| Create | `tests/integration/test_trends.py` | Multi-run fixture, test all 3 query functions |

## Out of Scope

- Cross-source URL dedup (deferred)
- Quarterly reports (R3.1)
- Custom CLI profile flags (R3.1)
- Score trend for individual items (items are deduped across runs, so the same item doesn't get re-scored)
