"""
PDF formatter — styled triage brief using fpdf2 (pure Python, no system deps).
"""
from __future__ import annotations

from collections import Counter
from datetime import date

from fpdf import FPDF

from src.module1_scanner.models import ScanItem
from src.module2_scorer.models import ScoreCard

_TRIAGE_COLOURS = {
    "Act Now":       (255, 68, 68),
    "Watch":         (255, 140, 0),
    "Monitor":       (255, 215, 0),
    "For Awareness": (144, 238, 144),
    "Low Signal":    (211, 211, 211),
}

_TRIAGE_ORDER = ["Act Now", "Watch", "Monitor", "For Awareness", "Low Signal"]

_TRIAGE_TEXT = {
    "Act Now":       "[!]",
    "Watch":         "[W]",
    "Monitor":       "[M]",
    "For Awareness": "[A]",
    "Low Signal":    "[L]",
}


def _clean(text: str) -> str:
    """Replace non-Latin-1 characters so fpdf2 Helvetica can render them."""
    replacements = {
        "\u2018": "'", "\u2019": "'",   # curly single quotes
        "\u201c": '"', "\u201d": '"',   # curly double quotes
        "\u2013": "-", "\u2014": "--",  # en-dash, em-dash
        "\u2026": "...",                # ellipsis
        "\u00a0": " ",                  # non-breaking space
        "\u200b": "",                   # zero-width space
        "\u00b7": "-",                  # middle dot
        "\u2022": "-",                  # bullet
        "\u2032": "'", "\u2033": '"',   # prime, double prime
        "\u00ae": "(R)", "\u2122": "(TM)", "\u00a9": "(C)",
        "\u03b1": "alpha", "\u03b2": "beta", "\u03b3": "gamma",
        "\u2264": "<=", "\u2265": ">=", "\u2260": "!=",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # Drop any remaining non-Latin-1 characters
    return text.encode("latin-1", errors="replace").decode("latin-1")


class _BriefPDF(FPDF):
    """Custom PDF with header/footer for the horizon scanning brief."""

    def __init__(self, run_meta: dict):
        super().__init__(orientation="P", unit="mm", format="A4")
        self.run_meta = run_meta
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(255, 255, 255)
        self.set_y(4)
        run_date = self.run_meta.get("run_date", str(date.today()))
        self.cell(0, 10, f"Horizon Scanning Brief - {run_date}", align="C")
        self.ln(14)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        profile = self.run_meta.get("profile_name", "")
        self.cell(0, 10, f"Horizon Scanning v2  |  {profile}  |  Page {self.page_no()}/{{nb}}", align="C")


def format_pdf(
    scorecards: list[ScoreCard],
    items_by_id: dict[str, ScanItem],
    run_meta: dict,
) -> bytes:
    """Render a styled PDF brief. Returns raw PDF bytes."""

    paired = [
        (sc, items_by_id[sc.item_id])
        for sc in scorecards
        if sc.item_id in items_by_id
    ]

    triage_counts = Counter(sc.triage_level for sc, _ in paired)
    domain_counts = Counter(d for _, item in paired for d in item.domains)

    pdf = _BriefPDF(run_meta)
    pdf.alias_nb_pages()
    pdf.add_page()

    # ── Run info ──────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    profile = run_meta.get("profile_name", "")
    run_id = run_meta.get("run_id", "")
    pdf.cell(0, 5, f"Profile: {profile}   |   Run: {run_id}   |   Items: {len(paired)}", align="C")
    pdf.ln(10)

    # ── Triage summary cards ──────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 7, "Triage Summary", ln=True)
    pdf.ln(2)

    card_w = 36
    start_x = (210 - card_w * 5 - 4 * 3) / 2  # centered with 3mm gaps
    y_top = pdf.get_y()

    for i, level in enumerate(_TRIAGE_ORDER):
        x = start_x + i * (card_w + 3)
        r, g, b = _TRIAGE_COLOURS[level]
        count = triage_counts.get(level, 0)

        # Card background
        pdf.set_fill_color(r, g, b)
        pdf.rect(x, y_top, card_w, 18, "F")

        # Border top accent
        pdf.set_draw_color(max(r - 40, 0), max(g - 40, 0), max(b - 40, 0))
        pdf.line(x, y_top, x + card_w, y_top)

        # Count
        pdf.set_xy(x, y_top + 1)
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(card_w, 9, str(count), align="C")

        # Label
        pdf.set_xy(x, y_top + 10)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(card_w, 6, level, align="C")

    pdf.set_y(y_top + 24)

    # ── Top items ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 7, "Top Items by Score", ln=True)
    pdf.ln(1)

    # Table header
    col_widths = [22, 85, 25, 18, 18, 22]  # triage, title, source, date, score, action-hint
    headers = ["Triage", "Title", "Source", "Date", "Score", "Tier"]

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    for j, hdr in enumerate(headers):
        pdf.cell(col_widths[j], 7, hdr, border=1, fill=True, align="C")
    pdf.ln()

    # Table rows (top 20)
    pdf.set_font("Helvetica", "", 7.5)
    for sc, item in paired[:20]:
        r, g, b = _TRIAGE_COLOURS.get(sc.triage_level, (238, 238, 238))
        pdf.set_fill_color(r, g, b)
        pdf.set_text_color(0, 0, 0)

        row_data = [
            _TRIAGE_TEXT.get(sc.triage_level, "") + " " + sc.triage_level,
            _clean(item.title[:70] + ("..." if len(item.title) > 70 else "")),
            _clean(item.source_name[:20]),
            str(item.published_date),
            f"{sc.composite_score:.1f}",
            item.horizon_tier,
        ]

        max_h = 6
        for j, val in enumerate(row_data):
            pdf.cell(col_widths[j], max_h, val, border=1, fill=(j == 0), align="L" if j == 1 else "C")
        pdf.ln()

    pdf.ln(4)

    # ── Domain breakdown ──────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 7, "Domain Breakdown", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 7, "Domain", border=1, fill=True)
    pdf.cell(30, 7, "Items", border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(0, 0, 0)
    for domain, count in domain_counts.most_common():
        pdf.cell(80, 6, domain, border=1)
        pdf.cell(30, 6, str(count), border=1, align="C")
        pdf.ln()

    pdf.ln(4)

    # ── Full item details ─────────────────────────────────────────────────
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 7, f"All Scored Items ({len(paired)})", ln=True)
    pdf.ln(2)

    for idx, (sc, item) in enumerate(paired):
        # Check if we need a new page (need ~35mm for an item block)
        if pdf.get_y() > 250:
            pdf.add_page()

        r, g, b = _TRIAGE_COLOURS.get(sc.triage_level, (238, 238, 238))

        # Triage colour bar
        pdf.set_fill_color(r, g, b)
        pdf.rect(pdf.get_x(), pdf.get_y(), 3, 24, "F")

        x_start = pdf.get_x() + 5
        y_start = pdf.get_y()

        # Title line
        pdf.set_xy(x_start, y_start)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(0, 0, 0)
        title_text = _clean(item.title[:100] + ("..." if len(item.title) > 100 else ""))
        pdf.cell(0, 5, title_text, ln=True)

        # Meta line
        pdf.set_x(x_start)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(80, 80, 80)
        preprint_tag = "  [PREPRINT]" if item.is_preprint else ""
        triage_tag = _TRIAGE_TEXT.get(sc.triage_level, "")
        meta = f"{triage_tag} {sc.triage_level}  |  Score: {sc.composite_score:.1f}  |  {_clean(item.source_name)}  |  {item.published_date}{preprint_tag}"
        pdf.cell(0, 4, meta, ln=True)

        # Scores line
        pdf.set_x(x_start)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 100, 100)
        scores = f"A={sc.evidence_strength:.0f}  B={sc.clinical_impact:.0f}  C={sc.insurance_readiness:.0f}  D={sc.domain_relevance:.0f}  |  Domains: {', '.join(item.domains)}"
        pdf.cell(0, 4, scores, ln=True)

        # Annotation
        pdf.set_x(x_start)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(60, 60, 60)
        annotation = _clean(sc.annotation[:150] + ("..." if len(sc.annotation) > 150 else ""))
        pdf.cell(0, 4, annotation, ln=True)

        # Action
        pdf.set_x(x_start)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(26, 107, 181)
        pdf.cell(0, 4, _clean(f"Action: {sc.suggested_action}"), ln=True)

        pdf.ln(3)

    return pdf.output()
