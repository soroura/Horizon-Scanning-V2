"""
Horizon Scanning Platform v2 — Streamlit dashboard.
Run: streamlit run app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on the path when running via streamlit
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st

st.set_page_config(
    page_title="Horizon Scanning v2",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.module3_reporter.trend import (
    get_items_df, get_triage_summary, get_domain_breakdown,
    get_source_health_df, get_new_topics_df, get_domain_trends_df, get_gap_analysis,
)
from src.database import DEFAULT_DB_PATH

# ── Triage colour map ─────────────────────────────────────────────────────────
TRIAGE_COLOURS = {
    "Act Now":       "#FF4444",
    "Watch":         "#FF8C00",
    "Monitor":       "#FFD700",
    "For Awareness": "#90EE90",
    "Low Signal":    "#D3D3D3",
}
TRIAGE_ORDER = ["Act Now", "Watch", "Monitor", "For Awareness", "Low Signal"]
TRIAGE_EMOJI = {
    "Act Now": "🔴", "Watch": "🟠", "Monitor": "🟡",
    "For Awareness": "🟢", "Low Signal": "⚪",
}


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> dict:
    st.sidebar.title("🔭 Horizon Scanning v2")
    st.sidebar.markdown("---")

    db_path = st.sidebar.text_input(
        "Database path",
        value=str(DEFAULT_DB_PATH),
        help="Path to scan_history.db",
    )

    date_range = st.sidebar.radio(
        "Date range",
        options=[7, 30, 90, 180, 365, 1825],
        index=4,
        format_func=lambda x: {7: "Last 7 days", 30: "Last 30 days", 90: "Last 90 days", 180: "Last 6 months", 365: "Last 1 year", 1825: "Last 5 years"}.get(x, f"Last {x} days"),
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filters")

    triage_filter = st.sidebar.multiselect(
        "Triage levels",
        options=TRIAGE_ORDER,
        default=TRIAGE_ORDER,
    )

    domain_filter = st.sidebar.multiselect(
        "Domains",
        options=["ai_health", "digital_health", "fda_regulatory"],
        default=[],
        help="Leave empty to show all",
    )

    horizon_filter = st.sidebar.multiselect(
        "Horizon tiers",
        options=["H1", "H2", "H3", "H4"],
        default=[],
        help="Leave empty to show all",
    )

    return {
        "db_path": Path(db_path),
        "days": date_range,
        "triage_filter": triage_filter or TRIAGE_ORDER,
        "domain_filter": domain_filter or None,
        "horizon_filter": horizon_filter or None,
    }


# ── Triage summary header ─────────────────────────────────────────────────────

def render_triage_summary(db_path: Path, days: int):
    counts = get_triage_summary(db_path, days=days)
    cols = st.columns(5)
    for col, level in zip(cols, TRIAGE_ORDER):
        emoji = TRIAGE_EMOJI[level]
        col.metric(f"{emoji} {level}", counts.get(level, 0))


# ── Scatter plot ──────────────────────────────────────────────────────────────

def render_scatter(df):
    if df.empty:
        return

    import plotly.express as px

    colour_map = {level: TRIAGE_COLOURS[level] for level in TRIAGE_ORDER}

    fig = px.scatter(
        df,
        x="evidence_strength",
        y="clinical_impact",
        color="triage_level",
        color_discrete_map=colour_map,
        hover_data=["title", "composite_score", "source_name", "published_date"],
        labels={
            "evidence_strength": "Evidence Strength (A)",
            "clinical_impact": "Clinical Impact (B)",
            "triage_level": "Triage",
        },
        title="Evidence Strength vs Clinical Impact",
        size_max=12,
    )
    fig.update_traces(marker=dict(size=10, opacity=0.8))
    fig.update_layout(height=420, legend_title_text="Triage Level")
    st.plotly_chart(fig, use_container_width=True)


# ── Item list + detail (click row to see details) ───────────────────────────

def render_item_list_and_detail(df):
    if df.empty:
        st.info("No items match the current filters. Try widening the date range or adjusting filters.")
        return

    df = df.copy()
    df["triage_emoji"] = df["triage_level"].map(TRIAGE_EMOJI)
    df["title_short"] = df["title"].str[:90]

    display_df = df[["triage_emoji", "title_short", "source_name", "published_date",
                      "composite_score", "triage_level", "horizon_tier", "is_preprint"]].rename(
        columns={
            "triage_emoji": "",
            "title_short": "Title",
            "source_name": "Source",
            "published_date": "Published",
            "composite_score": "Score",
            "triage_level": "Triage",
            "horizon_tier": "Tier",
            "is_preprint": "Preprint",
        }
    )

    # Clickable table — select a row to see details below
    event = st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Show detail for selected row
    selected_rows = event.selection.rows if event.selection else []
    if not selected_rows:
        st.caption("Click a row above to see item details.")
        return

    row = df.iloc[selected_rows[0]]

    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {row['title']}")
        preprint_badge = " ⚠️ **PREPRINT**" if row.get("is_preprint") else ""
        st.markdown(
            f"**Source**: {row['source_name']} | **Published**: {row['published_date']} "
            f"| **Horizon**: {row['horizon_tier']}{preprint_badge}"
        )
        st.markdown(f"> {row.get('annotation', '')}")
        st.markdown(f"**Suggested action**: {row.get('suggested_action', '')}")
        if row.get("url"):
            st.markdown(f"[Open source]({row['url']})")

    with col2:
        st.markdown("**Dimension Scores**")
        scores = {
            "A: Evidence": row["evidence_strength"],
            "B: Impact":   row["clinical_impact"],
            "C: Insurance": row["insurance_readiness"],
            "D: Relevance": row["domain_relevance"],
        }
        for label, score in scores.items():
            st.progress(int(score), text=f"{label}: {score:.0f}/100")
        st.metric("Composite Score", f"{row['composite_score']:.1f}/100")
        st.markdown(f"**Triage**: {TRIAGE_EMOJI.get(row['triage_level'], '')} {row['triage_level']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    filters = render_sidebar()

    st.title("🔭 Horizon Scanning Intelligence Dashboard")
    st.caption(f"Last {filters['days']} days · {filters['db_path']}")

    # Check if DB exists
    if not filters["db_path"].exists():
        st.warning(
            f"Database not found at `{filters['db_path']}`. "
            "Run `python -m v2.main scan` first to populate it."
        )
        return

    # Triage summary
    st.subheader("Triage Summary")
    render_triage_summary(filters["db_path"], filters["days"])

    # Load data with filters
    df = get_items_df(
        db_path=filters["db_path"],
        days=filters["days"],
        domains=filters.get("domain_filter"),
        triage_levels=filters.get("triage_filter"),
        horizon_tiers=filters.get("horizon_filter"),
    )

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Item List", "📊 Score Chart", "🏥 Source Health", "📈 Trends"])

    with tab1:
        st.caption(f"{len(df)} items")
        render_item_list_and_detail(df)

    with tab2:
        render_scatter(df)

    with tab3:
        health_df = get_source_health_df(db_path=filters["db_path"])
        if health_df.empty:
            st.info("No source health data yet. Run a scan first.")
        else:
            display = health_df[["source_name", "status", "items_count", "duration_ms", "error_message"]].copy()
            display["duration_s"] = (display["duration_ms"] / 1000).round(1)
            display = display.drop(columns=["duration_ms"])
            display = display.rename(columns={
                "source_name": "Source",
                "status": "Status",
                "items_count": "Items",
                "duration_s": "Time (s)",
                "error_message": "Error",
            })
            st.dataframe(display, use_container_width=True, hide_index=True)

            ok_count = len(health_df[health_df["status"] == "ok"])
            warn_count = len(health_df[health_df["status"] == "warn"])
            error_count = len(health_df[health_df["status"] == "error"])
            cols = st.columns(3)
            cols[0].metric("✅ OK", ok_count)
            cols[1].metric("⚠️ Warn", warn_count)
            cols[2].metric("❌ Error", error_count)

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


if __name__ == "__main__":
    main()
