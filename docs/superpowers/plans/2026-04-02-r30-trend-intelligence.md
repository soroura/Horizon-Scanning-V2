# R3.0 — Trend Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add cross-run trend analysis: new topic detection, domain score trends, coverage gap analysis, and a dashboard Trends tab.

**Architecture:** Three new query functions in `trend.py` operating on existing SQLite data (no schema changes). Results surface in the Markdown brief and a new Streamlit tab. A multi-run test fixture validates queries against synthetic data.

**Tech Stack:** Python 3.11+, pandas, sqlite-utils, plotly, Streamlit, Jinja2

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `src/module3_reporter/trend.py` | Add `get_new_topics_df()`, `get_domain_trends_df()`, `get_gap_analysis()` |
| Create | `tests/integration/test_trends.py` | Multi-run fixture + tests for all 3 functions |
| Modify | `src/module3_reporter/templates/digest.md.j2` | Add "New This Period" and "Coverage Gaps" sections |
| Modify | `src/module3_reporter/formatters/markdown.py` | Pass trend data to template |
| Modify | `app.py` | Add Trends tab (4th tab) |
| Modify | `plan/IMPLEMENTATION_PLAN.md` | Mark R3.0 as delivered |

---

### Task 1: Add Trend Query Functions + Tests

**Files:**
- Modify: `src/module3_reporter/trend.py`
- Create: `tests/integration/test_trends.py`

- [ ] **Step 1: Create multi-run test fixture and write failing tests**

Create `tests/integration/test_trends.py`:

```python
"""Integration test — trend intelligence queries across multiple runs."""
from __future__ import annotations

import json
from datetime import date, datetime, timezone, timedelta
from uuid import uuid4

import pandas as pd
import pytest

from src.database import init_db, save_run_start, save_run_complete, save_items
from src.module1_scanner.models import ScanItem
from src.module2_scorer.engine import score_items
from tests.integration.conftest import make_scan_item


@pytest.fixture
def multi_run_db(tmp_path):
    """Create a DB with 2 runs: run_old (3 items) and run_new (4 items, 2 overlapping)."""
    db_path = tmp_path / "trends.db"
    db = init_db(db_path)
    now = datetime.now(tz=timezone.utc)

    # --- Run 1 (old): 3 items ---
    run_old = str(uuid4())
    save_run_start(db, run_old, "phase1_ai_digital", now - timedelta(days=14))

    old_items = [
        make_scan_item(
            source_id="pubmed", url="https://example.com/old-1",
            title="AI in Radiology Review",
            domains=["ai_health"], keywords_matched=["AI", "radiology"],
        ),
        make_scan_item(
            source_id="jmir", url="https://example.com/old-2",
            title="Telehealth Adoption Study",
            domains=["digital_health"], keywords_matched=["telehealth"],
        ),
        make_scan_item(
            source_id="fda", url="https://example.com/old-3",
            title="FDA AI Device Guidance",
            category="regulatory",
            domains=["ai_health"], keywords_matched=["FDA", "AI"],
        ),
    ]
    old_cards = score_items(old_items, "phase1_ai_digital")
    save_items(db, run_old, old_items, old_cards)
    save_run_complete(db, run_old, now - timedelta(days=14), 3, 3)

    # --- Run 2 (new): 4 items (2 overlap with run 1, 2 brand new) ---
    run_new = str(uuid4())
    save_run_start(db, run_new, "phase1_ai_digital", now)

    new_items = [
        # Overlapping with old run (same URLs)
        make_scan_item(
            source_id="pubmed", url="https://example.com/old-1",
            title="AI in Radiology Review",
            domains=["ai_health"], keywords_matched=["AI", "radiology"],
        ),
        make_scan_item(
            source_id="jmir", url="https://example.com/old-2",
            title="Telehealth Adoption Study",
            domains=["digital_health"], keywords_matched=["telehealth"],
        ),
        # New items (not in old run)
        make_scan_item(
            source_id="arxiv", url="https://example.com/new-1",
            title="Transformer Model for ECG Analysis",
            domains=["ai_health"], keywords_matched=["transformer", "ECG"],
            is_preprint=True, category="preprints",
        ),
        make_scan_item(
            source_id="nice", url="https://example.com/new-2",
            title="NICE Recommends Digital CBT Programme",
            category="hta",
            domains=["digital_health"], keywords_matched=["digital", "CBT"],
        ),
    ]
    new_cards = score_items(new_items, "phase1_ai_digital")
    save_items(db, run_new, new_items, new_cards)
    save_run_complete(db, run_new, now, 4, 4)

    return db_path, run_old, run_new


class TestNewTopics:
    def test_returns_dataframe(self, multi_run_db):
        from src.module3_reporter.trend import get_new_topics_df
        db_path, _, run_new = multi_run_db
        df = get_new_topics_df(db_path)
        assert isinstance(df, pd.DataFrame)

    def test_finds_new_items_only(self, multi_run_db):
        from src.module3_reporter.trend import get_new_topics_df
        db_path, _, _ = multi_run_db
        df = get_new_topics_df(db_path)
        titles = set(df["title"])
        assert "Transformer Model for ECG Analysis" in titles
        assert "NICE Recommends Digital CBT Programme" in titles
        assert "AI in Radiology Review" not in titles
        assert "Telehealth Adoption Study" not in titles

    def test_empty_db(self, tmp_path):
        from src.module3_reporter.trend import get_new_topics_df
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        df = get_new_topics_df(db_path)
        assert len(df) == 0


class TestDomainTrends:
    def test_returns_dataframe(self, multi_run_db):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path, _, _ = multi_run_db
        df = get_domain_trends_df(db_path)
        assert isinstance(df, pd.DataFrame)
        assert "domain" in df.columns
        assert "item_count" in df.columns
        assert "avg_score" in df.columns

    def test_has_both_runs(self, multi_run_db):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path, _, _ = multi_run_db
        df = get_domain_trends_df(db_path)
        assert df["run_id"].nunique() == 2

    def test_has_both_domains(self, multi_run_db):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path, _, _ = multi_run_db
        df = get_domain_trends_df(db_path)
        domains = set(df["domain"])
        assert "ai_health" in domains
        assert "digital_health" in domains

    def test_empty_db(self, tmp_path):
        from src.module3_reporter.trend import get_domain_trends_df
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        df = get_domain_trends_df(db_path)
        assert len(df) == 0


class TestGapAnalysis:
    def test_returns_dict(self, multi_run_db):
        from src.module3_reporter.trend import get_gap_analysis
        db_path, _, _ = multi_run_db
        gaps = get_gap_analysis(db_path)
        assert "category_gaps" in gaps
        assert "domain_gaps" in gaps
        assert isinstance(gaps["category_gaps"], list)
        assert isinstance(gaps["domain_gaps"], list)

    def test_empty_db(self, tmp_path):
        from src.module3_reporter.trend import get_gap_analysis
        db_path = tmp_path / "empty.db"
        init_db(db_path)
        gaps = get_gap_analysis(db_path)
        assert gaps["category_gaps"] == []
        assert gaps["domain_gaps"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/integration/test_trends.py -v`
Expected: FAIL — `ImportError: cannot import name 'get_new_topics_df'`

- [ ] **Step 3: Implement the three query functions in trend.py**

Add to the end of `src/module3_reporter/trend.py`:

```python
def get_new_topics_df(
    db_path: Path = DEFAULT_DB_PATH,
    run_id: str | None = None,
) -> pd.DataFrame:
    """Return items from the latest run that don't appear in any previous run."""
    db = init_db(db_path)

    if run_id is None:
        row = db.execute("SELECT run_id FROM scan_runs ORDER BY started_at DESC LIMIT 1").fetchone()
        if not row:
            return pd.DataFrame()
        run_id = row[0]

    query = """
        SELECT si.*
        FROM scan_items si
        WHERE si.run_id = ?
        AND si.item_id NOT IN (
            SELECT item_id FROM scan_items WHERE run_id != ?
        )
        ORDER BY si.composite_score DESC
    """
    df = pd.read_sql_query(query, db.conn, params=[run_id, run_id])
    return df


def get_domain_trends_df(
    db_path: Path = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    """Return per-domain stats per run: item_count, avg_score."""
    db = init_db(db_path)

    query = """
        SELECT sr.run_id, sr.started_at as run_date, si.domains, si.composite_score
        FROM scan_items si
        JOIN scan_runs sr ON si.run_id = sr.run_id
        ORDER BY sr.started_at
    """
    raw_df = pd.read_sql_query(query, db.conn)
    if raw_df.empty:
        return pd.DataFrame(columns=["run_id", "run_date", "domain", "item_count", "avg_score"])

    # Explode JSON domains into separate rows
    raw_df["domains_list"] = raw_df["domains"].apply(lambda x: json.loads(x) if x else [])
    rows = []
    for _, row in raw_df.iterrows():
        for domain in row["domains_list"]:
            rows.append({
                "run_id": row["run_id"],
                "run_date": row["run_date"],
                "domain": domain,
                "composite_score": row["composite_score"],
            })

    if not rows:
        return pd.DataFrame(columns=["run_id", "run_date", "domain", "item_count", "avg_score"])

    exploded = pd.DataFrame(rows)
    grouped = exploded.groupby(["run_id", "run_date", "domain"]).agg(
        item_count=("composite_score", "count"),
        avg_score=("composite_score", "mean"),
    ).reset_index()
    grouped["avg_score"] = grouped["avg_score"].round(1)

    return grouped


def get_gap_analysis(
    db_path: Path = DEFAULT_DB_PATH,
) -> dict[str, list[str]]:
    """
    Compare active source categories against latest run results.
    Returns category_gaps (active categories with 0 items) and
    domain_gaps (domains in previous runs but not latest).
    """
    db = init_db(db_path)

    # Get latest run
    row = db.execute("SELECT run_id FROM scan_runs ORDER BY started_at DESC LIMIT 1").fetchone()
    if not row:
        return {"category_gaps": [], "domain_gaps": []}
    latest_run = row[0]

    # Categories present in latest run
    cat_rows = db.execute(
        "SELECT DISTINCT category FROM scan_items WHERE run_id = ?", [latest_run]
    ).fetchall()
    latest_categories = {r[0] for r in cat_rows}

    # All categories that have ever produced items
    all_cat_rows = db.execute("SELECT DISTINCT category FROM scan_items").fetchall()
    all_categories = {r[0] for r in all_cat_rows}

    category_gaps = sorted(all_categories - latest_categories)

    # Domains in previous runs but not in latest
    prev_domain_rows = db.execute(
        "SELECT DISTINCT domains FROM scan_items WHERE run_id != ?", [latest_run]
    ).fetchall()
    prev_domains: set[str] = set()
    for r in prev_domain_rows:
        for d in json.loads(r[0] or "[]"):
            prev_domains.add(d)

    latest_domain_rows = db.execute(
        "SELECT DISTINCT domains FROM scan_items WHERE run_id = ?", [latest_run]
    ).fetchall()
    latest_domains: set[str] = set()
    for r in latest_domain_rows:
        for d in json.loads(r[0] or "[]"):
            latest_domains.add(d)

    domain_gaps = sorted(prev_domains - latest_domains)

    return {"category_gaps": category_gaps, "domain_gaps": domain_gaps}
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/integration/test_trends.py -v`
Expected: All 10 tests pass

- [ ] **Step 5: Run full suite**

Run: `pytest tests/ -q --tb=short`
Expected: All 120 tests pass

- [ ] **Step 6: Commit**

```bash
git add src/module3_reporter/trend.py tests/integration/test_trends.py
git commit -m "feat(R3.0): add new topics, domain trends, gap analysis queries"
```

---

### Task 2: Add Trend Sections to Markdown Brief

**Files:**
- Modify: `src/module3_reporter/templates/digest.md.j2`
- Modify: `src/module3_reporter/formatters/markdown.py`

- [ ] **Step 1: Add trend sections to Jinja2 template**

In `src/module3_reporter/templates/digest.md.j2`, add this after the SOURCE HEALTH section (before `## FULL ITEM LIST`):

```jinja2
{% if new_topics %}
---

## NEW THIS PERIOD ({{ new_topics | length }} items)

{% for item in new_topics[:10] %}
- **{{ item.title | truncate(100) }}** — Score: {{ item.composite_score }}/100 | {{ item.source_name }} | {{ item.published_date }}
{% endfor %}
{% if new_topics | length > 10 %}
_... and {{ new_topics | length - 10 }} more new items._
{% endif %}

{% endif %}
{% if category_gaps or domain_gaps %}
---

## COVERAGE GAPS

{% if category_gaps %}
**Categories with no items this period:** {{ category_gaps | join(", ") }}
{% endif %}
{% if domain_gaps %}
**Domains declining (present before, absent now):** {{ domain_gaps | join(", ") }}
{% endif %}

{% endif %}
```

- [ ] **Step 2: Pass trend data to template in markdown.py**

In `src/module3_reporter/formatters/markdown.py`, add imports and query calls before `template.render()`. Add these lines inside the `format_markdown` function, before the `return template.render(` line:

```python
    # Trend data (optional — only if run_meta has db_path)
    new_topics_data = []
    category_gaps = []
    domain_gaps = []
    db_path = run_meta.get("db_path")
    if db_path:
        from src.module3_reporter.trend import get_new_topics_df, get_gap_analysis
        nt_df = get_new_topics_df(db_path)
        if not nt_df.empty:
            new_topics_data = nt_df.to_dict("records")
        gaps = get_gap_analysis(db_path)
        category_gaps = gaps.get("category_gaps", [])
        domain_gaps = gaps.get("domain_gaps", [])
```

Then add these to the `template.render()` call:

```python
        new_topics=new_topics_data,
        category_gaps=category_gaps,
        domain_gaps=domain_gaps,
```

- [ ] **Step 3: Pass db_path in run_meta from main.py**

In `src/main.py`, in the `scan()` function, add `db_path` to the `run_meta` dict:

```python
    run_meta = {
        "run_id": run_id,
        "profile_name": profile,
        "run_date": started_at.strftime("%Y-%m-%d"),
        "sources_count": len(set(item.source_id for item in scan_items)),
        "source_health": source_results,
        "db_path": db_path,
    }
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/ -q --tb=short`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add src/module3_reporter/templates/digest.md.j2 src/module3_reporter/formatters/markdown.py src/main.py
git commit -m "feat(R3.0): add new topics and coverage gaps to Markdown brief"
```

---

### Task 3: Add Trends Tab to Streamlit Dashboard

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Update imports in app.py**

Change the import line from:
```python
from src.module3_reporter.trend import get_items_df, get_triage_summary, get_domain_breakdown, get_source_health_df
```
to:
```python
from src.module3_reporter.trend import (
    get_items_df, get_triage_summary, get_domain_breakdown,
    get_source_health_df, get_new_topics_df, get_domain_trends_df, get_gap_analysis,
)
```

- [ ] **Step 2: Add 4th tab**

Change the tabs line from:
```python
    tab1, tab2, tab3 = st.tabs(["📋 Item List", "📊 Score Chart", "🏥 Source Health"])
```
to:
```python
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Item List", "📊 Score Chart", "🏥 Source Health", "📈 Trends"])
```

- [ ] **Step 3: Add Trends tab content**

After the `with tab3:` block, add:

```python
    with tab4:
        import plotly.express as px

        # --- Domain trends line chart ---
        trends_df = get_domain_trends_df(db_path=filters["db_path"])
        if not trends_df.empty and trends_df["run_id"].nunique() > 1:
            st.subheader("Items per Domain Over Time")
            fig = px.line(
                trends_df,
                x="run_date",
                y="item_count",
                color="domain",
                markers=True,
                labels={"run_date": "Run Date", "item_count": "Items", "domain": "Domain"},
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)
        elif not trends_df.empty:
            st.info("Run at least 2 scans to see domain trends over time.")

        # --- New topics ---
        st.subheader("New This Period")
        new_df = get_new_topics_df(db_path=filters["db_path"])
        if new_df.empty:
            st.info("No new topics detected (all items were seen in previous runs, or this is the first run).")
        else:
            display = new_df[["title", "source_name", "composite_score", "triage_level", "published_date"]].head(20).copy()
            display = display.rename(columns={
                "title": "Title", "source_name": "Source",
                "composite_score": "Score", "triage_level": "Triage",
                "published_date": "Published",
            })
            st.dataframe(display, use_container_width=True, hide_index=True)
            st.caption(f"{len(new_df)} new items total")

        # --- Gap analysis ---
        gaps = get_gap_analysis(db_path=filters["db_path"])
        if gaps["category_gaps"] or gaps["domain_gaps"]:
            st.subheader("Coverage Gaps")
            if gaps["category_gaps"]:
                st.warning(f"**Categories with no items this period:** {', '.join(gaps['category_gaps'])}")
            if gaps["domain_gaps"]:
                st.warning(f"**Domains declining:** {', '.join(gaps['domain_gaps'])}")
        else:
            st.success("No coverage gaps detected.")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/ -q --tb=short`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add app.py
git commit -m "feat(R3.0): add Trends tab to Streamlit dashboard"
```

---

### Task 4: Update Implementation Plan

**Files:**
- Modify: `plan/IMPLEMENTATION_PLAN.md`

- [ ] **Step 1: Mark R3.0 as delivered**

Update the R3.0 section header to `*(DELIVERED)*`. Mark deliverables R3.0-01 through R3.0-04 as Done, R3.0-05 as Deferred. Update the timeline diagram to show R3.0 complete and move current position to R3.1.

- [ ] **Step 2: Commit**

```bash
git add plan/IMPLEMENTATION_PLAN.md
git commit -m "docs(R3.0): mark trend intelligence release as delivered"
```
