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

from src.module3_reporter.trend import get_items_df, get_triage_summary, get_domain_breakdown
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
        options=[7, 30, 90],
        index=1,
        format_func=lambda x: f"Last {x} days",
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
        options=["ai_health", "digital_health"],
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


# ── Item list ────────────────────────────────────────────────────────────────

def render_item_list(df):
    if df.empty:
        st.info("No items match the current filters. Try widening the date range or adjusting filters.")
        return

    display_cols = [
        "triage_emoji", "title", "source_name",
        "published_date", "composite_score", "triage_level",
    ]
    # Add triage_emoji derived column
    df = df.copy()
    df["triage_emoji"] = df["triage_level"].map(TRIAGE_EMOJI)
    df["title_short"] = df["title"].str[:90]

    st.dataframe(
        df[["triage_emoji", "title_short", "source_name", "published_date",
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
        ),
        use_container_width=True,
        hide_index=True,
    )


# ── Item detail pane ─────────────────────────────────────────────────────────

def render_item_detail(df):
    if df.empty:
        return

    st.markdown("---")
    st.subheader("Item Detail")

    titles = df["title"].str[:100].tolist()
    selected = st.selectbox("Select an item to view details:", options=titles, index=0)

    row = df[df["title"].str[:100] == selected].iloc[0]

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

    tab1, tab2 = st.tabs(["📋 Item List", "📊 Score Chart"])

    with tab1:
        st.caption(f"{len(df)} items")
        render_item_list(df)
        render_item_detail(df)

    with tab2:
        render_scatter(df)


if __name__ == "__main__":
    main()
