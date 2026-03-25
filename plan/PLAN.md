# Horizon Scanning Platform — Version 2 Design Plan

**Status:** Planning
**Date:** 2026-03-25
**Author:** Ahmed Sorour / WHO Egypt
**Built for:** Bupa Clinical Intelligence

---

## Vision

Version 1 proved the concept: automated scanning of 30+ sources produces actionable clinical intelligence. Version 2 moves from a script to a **platform** — modular, configurable, extensible, with visual output and a disciplined scoring model.

The platform has three self-contained modules that can be run independently or as a pipeline:

```
┌──────────────────────────────────────────────────────────────┐
│                  HORIZON SCANNING PLATFORM v2                │
├──────────────┬──────────────────────┬────────────────────────┤
│  MODULE 1    │     MODULE 2         │      MODULE 3          │
│  SCANNING    │     SCORING          │  REPORTING &           │
│              │                      │  VISUALISATION         │
│  What's new? │  Does it matter?     │  Show the picture      │
└──────────────┴──────────────────────┴────────────────────────┘
```

---

## Phase 1 Focus: AI in Health & Digital Health

Before the general medical scanner runs, **Phase 1 targets two domains** that are evolving faster than traditional clinical evidence cycles:

1. **AI in health and social care** — clinical AI tools, diagnostic AI, AI-assisted decision support, AI regulation (FDA/EMA/MHRA AI frameworks), AI safety in medicine
2. **Digital health and health information systems** — electronic health records, interoperability standards (HL7 FHIR, IHE), patient-facing apps, wearables evidence, telehealth policy, national health IT programmes

These domains require a **different source mix** (regulatory/policy + technical standards + peer review) and a **different relevance framework** (adoption readiness, regulatory status, clinical validation stage) compared to traditional drug/guideline scanning.

Phase 1 sources and scoring weights are defined in Module 1 and Module 2 respectively.

---

## Module 1: Scanning

### Purpose

Systematically ingest new published content from structured sources, returning a normalised database of items with full metadata. The scanner does not judge — it collects.

### 1.1 Source Database

Built from the catalogue in `research 20-mar/compass_artifact_wf-94488947-5779-455c-9c5a-5bc5c47e1e84_text_markdown.md` (120+ sources) plus Phase 1 additions. Sources are stored in `version2/config/sources.yaml` with the schema below.

#### Source record schema

```yaml
sources:
  - id: pubmed_eutils             # unique snake_case identifier
    name: "PubMed E-utilities"
    category: aggregator          # see Category taxonomy below
    url: "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    feed_type: api                # api | rss | web_scrape | download
    feed_url: "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    access: free                  # free | free_registration | subscription
    auth_required: false
    update_frequency: continuous  # continuous | daily | weekly | monthly
    domains:
      - general
      - ai_health
      - digital_health
    horizon_tier: H3              # H1 (confirmed) to H4 (early signal)
    programmatic_access: full     # full | rss_only | download_only | manual
    priority_rank: 1              # 1–30 from catalogue; null for new sources
    notes: ""
    active: true
```

#### Category taxonomy (10 categories from catalogue + 2 Phase 1 additions)

| Code | Category |
|------|----------|
| `regulatory` | Regulatory approval bodies (FDA, EMA, MHRA, TGA, Health Canada) |
| `guidelines` | Clinical guideline bodies (NICE, ESC, ACC/AHA, ASCO, ESMO, NCCN, IDSA, USPSTF) |
| `journals` | Peer-reviewed journals (NEJM, Lancet, BMJ, JAMA, etc.) |
| `trials` | Clinical trial registries (ClinicalTrials.gov, EU CTIS, ISRCTN, ICTRP) |
| `news` | Medical news aggregators (Medscape, STAT, MedPage, Fierce) |
| `preprints` | Preprint servers (medRxiv, bioRxiv) |
| `safety` | Drug safety / pharmacovigilance (MedWatch, EMA PRAC, DailyMed) |
| `hta` | Health technology assessment bodies (NICE TA, CADTH, PBAC, IQWiG) |
| `aggregator` | Literature aggregators (PubMed, Europe PMC, Cochrane, Trip) |
| `specialty` | Specialty-specific sources (NCI, AHA Journals, CDC EID, ECDC, ProMED) |
| `ai_digital` | **[Phase 1]** AI / digital health sources (see §1.2) |
| `standards` | **[Phase 1]** Interoperability and HIT standards bodies (HL7, IHE, SNOMED) |

### 1.2 Phase 1 Source List — AI & Digital Health

These sources are not in the original catalogue and are added for Phase 1.

| Source | URL | Feed/API | Access | Horizon Tier |
|--------|-----|----------|--------|--------------|
| **FDA Digital Health Centre of Excellence** | https://www.fda.gov/medical-devices/digital-health-center-excellence | RSS | Free | H1/H2 |
| **FDA AI/ML-Based SaMD Action Plan** | https://www.fda.gov/medical-devices/software-medical-device-samd | RSS | Free | H1 |
| **MHRA AI and Digital Regulation** | https://www.gov.uk/government/organisations/medicines-and-healthcare-products-regulatory-agency | GOV.UK RSS | Free | H1/H2 |
| **NICE Evidence Standards for Digital Health** | https://www.nice.org.uk/about/what-we-do/our-programmes/evidence-standards-framework-for-digital-health-technologies | NICE API | Free (API licence) | H1 |
| **WHO Digital Health** | https://www.who.int/health-topics/digital-health | WHO RSS | Free | H1/H2 |
| **NHS Digital / NHS England Tech** | https://transform.england.nhs.uk/ | GOV.UK RSS | Free | H1/H2 |
| **HL7 International** | https://www.hl7.org/news/ | RSS | Free | H2 |
| **IHE International** | https://www.ihe.net/news/ | RSS | Free | H2 |
| **Journal of Medical Internet Research (JMIR)** | https://www.jmir.org/ | ✅ RSS: `jmir.org/feed/` | OA (CC BY) | H2/H3 |
| **npj Digital Medicine** | https://www.nature.com/npjdigitalmed/ | ✅ `nature.com/npjdigitalmed.rss` | OA (Springer Nature) | H2/H3 |
| **The Lancet Digital Health** | https://www.thelancet.com/journals/landig/home | ✅ RSS | OA | H2/H3 |
| **JAMIA** | https://academic.oup.com/jamia | ✅ RSS | Subscription/hybrid | H2/H3 |
| **Digital Health (SAGE)** | https://journals.sagepub.com/home/dhj | ✅ RSS | OA (CC BY) | H3 |
| **medRxiv — Health Informatics** | https://www.medrxiv.org | ✅ REST API (subject=health_informatics) | Free | H4 |
| **medRxiv — Health Policy** | https://www.medrxiv.org | ✅ REST API (subject=health_policy) | Free | H4 |
| **AHIMA (Health Information Management)** | https://www.ahima.org/publications-continuinged/ | Email/RSS | Free | H2 |
| **HIMSS News** | https://www.himss.org/news | RSS | Free | H2 |
| **ONC (US Office of National Coordinator)** | https://www.healthit.gov/newsroom/ | RSS | Free (public domain) | H1/H2 |
| **SNOMED International** | https://www.snomed.org/news/ | RSS | Free | H2 |
| **OpenEHR Foundation** | https://www.openehr.org/news/ | RSS | Free | H3 |
| **The Alan Turing Institute — Health** | https://www.turing.ac.uk/research/research-topics/health-and-medical-sciences | RSS | Free | H3/H4 |
| **Google DeepMind Health publications** | https://deepmind.google/research/publications/ | RSS | Free | H3/H4 |

### 1.2a AI Research Databases — dedicated sources for AI/ML literature

These are distinct from general medical journals. AI research moves faster than peer-review cycles; most landmark AI papers (including clinical AI) appear on preprint servers and conference proceedings **months before** journal publication. This section covers the primary databases where AI researchers publish.

#### arXiv — the central preprint server for AI/ML research

arXiv is the dominant publication venue for AI and machine learning research. Most foundational clinical AI papers (DeepMind's diabetic retinopathy, Google's breast cancer screening, LLM clinical reasoning) appeared on arXiv before any journal. It is **not a medical database** — it is a computer science / physics / statistics server — but it is where AI in health research lives before it reaches PubMed.

| arXiv Subject | Code | Relevance to health AI |
|---------------|------|------------------------|
| Artificial Intelligence | `cs.AI` | Clinical decision support, reasoning systems |
| Machine Learning | `cs.LG` | Core ML methods applied in health |
| Computer Vision | `cs.CV` | Medical imaging AI (radiology, pathology, ophthalmology) |
| Computation and Language | `cs.CL` | NLP for EHR, clinical notes, LLMs in medicine |
| Neural and Evolutionary Computing | `cs.NE` | Deep learning architectures |
| Image and Video Processing | `eess.IV` | Medical image processing specifically |
| Quantitative Biology — Quantitative Methods | `q-bio.QM` | Computational biology, bioinformatics |

**API access:** arXiv provides a free REST API (`export.arxiv.org/api/query`) returning Atom XML. No authentication required. Query syntax supports author, title, abstract, and category filtering. Rate limit: 3 requests/second.

Example query for health AI papers:
```
https://export.arxiv.org/api/query?search_query=cat:cs.LG+AND+(ti:clinical+OR+ti:medical+OR+ti:health)+AND+submittedDate:[20260301+TO+20260325]&max_results=50&sortBy=submittedDate&sortOrder=descending
```

**RSS feeds:** Each subject category has a daily RSS feed:
- `https://rss.arxiv.org/rss/cs.AI` — all new AI submissions
- `https://rss.arxiv.org/rss/cs.LG` — machine learning
- `https://rss.arxiv.org/rss/cs.CV` — computer vision
- `https://rss.arxiv.org/rss/eess.IV` — image processing

**Important caveats (same as medRxiv):**
- arXiv papers are **not peer-reviewed**; flag all arXiv items as `is_preprint: true`
- Quality varies enormously; scoring Dimension A (Evidence Strength) caps at 30 for arXiv items unless subsequently published in a peer-reviewed venue
- Cross-reference against PubMed/Semantic Scholar to detect when an arXiv paper has been published

#### Full Phase 1 AI database source list

| Source | URL | Feed / API | Access | Horizon Tier | Notes |
|--------|-----|------------|--------|--------------|-------|
| **arXiv cs.AI** | https://arxiv.org | ✅ REST API + RSS daily | Free | H4 | Primary AI preprint server |
| **arXiv cs.LG** | https://arxiv.org | ✅ REST API + RSS daily | Free | H4 | Machine learning papers |
| **arXiv cs.CV** | https://arxiv.org | ✅ REST API + RSS daily | Free | H4 | Medical imaging AI |
| **arXiv cs.CL** | https://arxiv.org | ✅ REST API + RSS daily | Free | H4 | NLP / LLMs in medicine |
| **arXiv eess.IV** | https://arxiv.org | ✅ REST API + RSS daily | Free | H4 | Medical image processing |
| **Semantic Scholar** | https://www.semanticscholar.org | ✅ REST API (S2 API): `api.semanticscholar.org/graph/v1/` | Free (API key) | H3/H4 | 200M+ papers; AI-powered relevance ranking; citation graphs |
| **Papers With Code** | https://paperswithcode.com | ✅ REST API: `paperswithcode.com/api/v1/` | Free | H3/H4 | Links ML papers to code + benchmarks; medical imaging section |
| **OpenReview** | https://openreview.net | ✅ REST API: `api2.openreview.net/notes` | Free | H3/H4 | Peer review for NeurIPS, ICLR, ICML proceedings — top AI conferences |
| **IEEE Xplore** | https://ieeexplore.ieee.org | ✅ REST API (key required): `ieeexploreapi.ieee.org/api/v1/` | API free (key); content subscription | H2/H3 | IEEE EMBC, EMBS journals; biomedical engineering + AI |
| **ACM Digital Library** | https://dl.acm.org | Limited API (OpenURL); RSS per conference | Subscription; abstracts free | H2/H3 | CHI, CSCW — human-computer interaction in health |
| **Hugging Face Papers** | https://huggingface.co/papers | ✅ REST API + RSS: `huggingface.co/papers.rss` | Free | H4 | Community-curated daily AI papers; often health AI featured |
| **Google Scholar Alerts** | https://scholar.google.com | ❌ No API; email alerts only | Free | H3/H4 | Configure alerts for "clinical AI", "medical LLM", "AI diagnosis" |
| **DBLP** | https://dblp.org | ✅ REST API + RSS: `dblp.org/rss/` | Free | H3/H4 | CS bibliography; useful for tracking specific authors and venues |
| **Elsevier ScienceDirect** | https://www.sciencedirect.com | ✅ Scopus API + Science Direct API (key required) | API free; content subscription | H2/H3 | Covers Artificial Intelligence journal, Pattern Recognition, Medical Image Analysis |
| **Springer Nature API** | https://dev.springernature.com | ✅ REST API (key required) | Free API key; content hybrid | H2/H3 | Nature Machine Intelligence, Scientific Reports — health AI papers |

#### Key AI conferences to monitor (proceedings via OpenReview / ACM / IEEE)

These conferences publish work that becomes clinical AI practice within 2–5 years. No RSS feeds — monitor via OpenReview API or Google Scholar alerts.

| Conference | Acronym | Relevance | Proceedings |
|------------|---------|-----------|------------|
| Neural Information Processing Systems | NeurIPS | Core ML methods | OpenReview API |
| International Conference on Learning Representations | ICLR | Deep learning | OpenReview API |
| International Conference on Machine Learning | ICML | Core ML | OpenReview API / PMLR |
| Medical Image Computing and Computer Assisted Intervention | MICCAI | Clinical imaging AI | Springer (IEEE) |
| AAAI Conference on AI | AAAI | Clinical AI, reasoning | ACM DL |
| ACM Conference on Health, Inference, and Learning | CHIL | Health AI specifically | ACM DL |
| Machine Learning for Healthcare | MLHC | Health AI specifically | PMLR |
| IEEE Engineering in Medicine and Biology | EMBC | Biomedical AI | IEEE Xplore |

#### Programmatic access notes

**Semantic Scholar API** is particularly valuable — it offers:
- `GET /paper/search?query=clinical+AI&fields=title,abstract,year,authors,citationCount` — semantic search across 200M papers
- Citation velocity (papers gaining citations fast = emerging important work)
- Author disambiguation and paper recommendation
- Free tier: 100 requests/5 minutes; `x-api-key` header increases to 1 request/second

**Papers With Code** API offers:
- `GET /api/v1/papers/?q=medical+imaging&has_github=true` — filter for papers with reproducible code
- `GET /api/v1/evaluations/` — benchmark results (e.g. ImageNet, medical image segmentation benchmarks)
- Useful for assessing whether a clinical AI method is reproducible and benchmark-validated

**OpenReview API v2** offers:
- `GET /notes?invitation=NeurIPS.cc/2025/Conference/-/Submission` — all submissions to a conference
- Filter by `venueid`, `content.keywords`, or `content.abstract` for health-related submissions
- Access to reviews and meta-reviews — a form of pre-publication peer assessment

### 1.3 Scanning Engine

#### Inputs

| Parameter       | Type | Default    | Description                                                        |
| --------------- | ---- | ---------- | ------------------------------------------------------------------ |
| `domains`       | list | `["all"]`  | Filter to specific domains (e.g. `["ai_health","digital_health"]`) |
| `days`          | int  | `30`       | Look-back window in days                                           |
| `sources`       | list | all active | Explicit list of source IDs to scan                                |
| `categories`    | list | all        | Filter by source category                                          |
| `horizon_tiers` | list | all        | Filter by H1–H4                                                    |

#### Processing pipeline (per source)

```
Fetch → Parse → Normalise → Date-filter → Deduplicate → Tag domains → Emit
```

Each emitted item conforms to the **ScanItem** schema:

```python
@dataclass
class ScanItem:
    # Identity
    id: str                    # SHA-256 of (source_id + url)
    source_id: str
    source_name: str
    category: str
    horizon_tier: str          # H1–H4

    # Content
    title: str
    url: str
    summary: str               # abstract / first 500 chars
    full_text: str | None      # if accessible

    # Metadata
    published_date: date
    retrieved_date: date
    authors: list[str]
    journal: str | None
    doi: str | None
    pmid: str | None

    # Domain tagging (applied by scanner)
    domains: list[str]         # e.g. ["ai_health", "cardiology"]
    keywords_matched: list[str]

    # Access
    access_model: str          # free | subscription | registration
    is_preprint: bool
```

#### Domain keyword banks (Phase 1)

The scanner uses keyword banks to tag items. Phase 1 banks:

**`ai_health`** (130+ terms)
- Diagnostic AI, clinical AI, machine learning in medicine, deep learning radiology, AI-assisted diagnosis, computer-aided detection, natural language processing EHR, large language model clinical, LLM healthcare, AI safety healthcare, algorithmic bias medicine, explainable AI clinical, regulatory AI medical device, SaMD, software as a medical device, AI clinical decision support, predictive analytics health, AI triage, AI pathology, AI dermatology, AI ophthalmology (diabetic retinopathy), AI cardiology, AI radiology, FDA AI, MHRA AI, CE marking AI, algorithm-based decision, automated image analysis, AI enabled device…

**`digital_health`** (100+ terms)
- Electronic health record, EHR, EMR, patient portal, digital therapeutics, DTx, mobile health, mHealth, telehealth, telemedicine, wearable, remote patient monitoring, digital biomarker, patient-generated data, health app, NHS app, connected care, digital care pathway, virtual ward, digital front door, digital inclusion, health equity digital, interoperability, HL7 FHIR, SMART on FHIR, IHE, clinical data exchange, fast healthcare interoperability resources, API healthcare, patient data, health information exchange, HIE, national health IT, electronic prescribing, e-prescribing, clinical coding, SNOMED CT, ICD-11, data standard health…

### 1.4 Source Database File

The full source database is maintained at:

```
version2/config/sources.yaml      # source definitions
version2/config/domains.yaml      # domain keyword banks
version2/config/scan_profiles.yaml # named scan configurations
```

#### Scan profiles

```yaml
profiles:
  phase1_ai_digital:
    name: "Phase 1 — AI & Digital Health"
    domains: [ai_health, digital_health]
    days: 30
    horizon_tiers: [H1, H2, H3]
    categories: [regulatory, guidelines, journals, ai_digital, standards, hta, news]

  full_scan:
    name: "Full medical intelligence scan"
    domains: [all]
    days: 30
    horizon_tiers: [H1, H2, H3, H4]
    categories: [all]

  safety_only:
    name: "Safety alerts only"
    domains: [all]
    days: 7
    horizon_tiers: [H1]
    categories: [safety, regulatory]
```

---

## Module 2: Scoring

### Purpose

Take each ScanItem and produce a **ScoreCard** — a structured assessment of how much this item matters and why. The scorer is domain-aware: scoring weights differ for AI/digital health vs traditional clinical evidence.

### 2.1 Scoring Dimensions

Every item is scored on four independent dimensions (0–100 each), then combined into a weighted total.

#### Dimension A — Evidence Strength (0–100)

Reflects the methodological quality of the source and publication type.

| Score | Evidence level | Examples |
|-------|---------------|---------|
| 90–100 | Regulatory decision / Guideline | FDA approval, NICE TA, RCT published in NEJM/Lancet |
| 70–89 | High-quality systematic evidence | Cochrane SR, large Phase 3 RCT, HTA recommendation |
| 50–69 | Moderate evidence | Prospective cohort, meta-analysis conference abstract, published guideline draft |
| 30–49 | Emerging / preliminary evidence | Phase 1–2 trial result, small observational study, expert consensus |
| 10–29 | Signal only | Preprint, case series, news report citing unpublished data |
| 0–9 | Anecdotal / opinion | Editorial, commentary, personal blog |

AI/digital health modifier:
- Peer-reviewed clinical validation study (prospective, real-world): +10
- Regulatory submission / CE mark / FDA clearance for an AI tool: +15
- Algorithm described but not clinically validated: −15

#### Dimension B — Clinical Practice Impact (0–100)

Will this change what a clinician **does today or in the near future**?

| Score | Meaning |
|-------|---------|
| 80–100 | Immediate practice change required or highly likely within 12 months |
| 60–79 | Likely practice change within 1–3 years; monitor and prepare |
| 40–59 | May influence practice in 3–5 years; awareness needed |
| 20–39 | Uncertain clinical translation; watch for follow-up evidence |
| 0–19 | No foreseeable direct clinical practice impact |

Sub-scores contributing to this dimension:
- Is there a regulatory approval or NICE/guideline endorsement? (weight 40%)
- Does it address a high-prevalence or high-burden condition? (weight 30%)
- Does it improve on an existing standard of care? (weight 20%)
- Is there an implementation pathway (training, pathway, procurement)? (weight 10%)

#### Dimension C — Insurance / Reimbursement Readiness (0–100)

Will insurers (including Bupa) need to cover this? Is it funded?

| Score | Meaning |
|-------|---------|
| 80–100 | Already reimbursed or HTA-recommended; Bupa must review coverage |
| 60–79 | HTA under review or likely to be submitted; proactive planning needed |
| 40–59 | Regulatory approved but no HTA decision yet; risk of off-label pressure |
| 20–39 | Clinical evidence emerging; no reimbursement pathway visible |
| 0–19 | Not on reimbursement radar |

Signals that raise this score:
- NICE TA positive / in development (+30)
- CADTH / PBAC positive recommendation (+20)
- Orphan drug designation (+10)
- FDA / EMA Breakthrough / PRIME designation (+10)
- Cost data published showing cost-effectiveness (+10)

#### Dimension D — Domain Relevance (0–100)

How well does this item match the active scan domain(s)?

Calculated by the keyword matching engine:
- Exact keyword match in title: high weight
- Keyword in abstract: medium weight
- Related-domain keyword: low weight
- Source category alignment: bonus

For Phase 1, items tagged `ai_health` or `digital_health` receive a domain relevance bonus of +20 before normalisation.

### 2.2 Composite Score

```
Composite = (A × w_A) + (B × w_B) + (C × w_C) + (D × w_D)
```

Default weights (adjustable per scan profile):

| Profile | w_A | w_B | w_C | w_D |
|---------|-----|-----|-----|-----|
| Phase 1 AI/Digital | 0.25 | 0.30 | 0.20 | 0.25 |
| Clinical (standard) | 0.30 | 0.35 | 0.25 | 0.10 |
| Safety focus | 0.40 | 0.35 | 0.15 | 0.10 |
| Insurance/HTA focus | 0.20 | 0.25 | 0.45 | 0.10 |

### 2.3 Triage Categories

| Label | Composite score | Action |
|-------|----------------|--------|
| 🔴 **Act Now** | ≥ 75 | Immediate clinical review; escalate to relevant lead |
| 🟠 **Watch** | 60–74 | Include in next weekly brief; assign reviewer |
| 🟡 **Monitor** | 45–59 | Include in monthly digest; log for trend tracking |
| 🟢 **For Awareness** | 25–44 | Archive; surface in quarterly summary |
| ⚪ **Low Signal** | < 25 | Archive only; do not surface in reports |

### 2.4 ScoreCard Schema

```python
@dataclass
class ScoreCard:
    item_id: str                  # links to ScanItem

    # Dimension scores (0–100)
    evidence_strength: float
    clinical_impact: float
    insurance_readiness: float
    domain_relevance: float

    # Composite
    composite_score: float
    triage_level: str             # Act Now / Watch / Monitor / For Awareness / Low Signal
    triage_emoji: str

    # Rationale (human-readable)
    evidence_notes: str
    impact_notes: str
    insurance_notes: str
    domain_notes: str

    # Clinical annotation (generated)
    annotation: str               # 1–2 sentence clinical intelligence summary
    suggested_action: str         # e.g. "Review formulary", "Update pathway", "Monitor trial"

    # Scoring metadata
    profile_used: str
    scored_at: datetime
    weights_used: dict
```

---

## Module 3: Reporting and Visualisation

### Purpose

Transform scored items into outputs that different audiences can act on — from a scanning analyst to a clinical lead to an executive.

### 3.1 Output Formats

| Format | Audience | Delivery |
|--------|----------|---------|
| **Markdown brief** | Clinical analyst | File export |
| **HTML dashboard** | Clinical / management | Browser / email |
| **Excel export** | Data analyst / clinical governance | `.xlsx` file |
| **JSON export** | API / downstream systems | `.json` file |
| **Email digest** | Any | HTML email |

### 3.2 Report Sections

#### A. Intelligence Brief (always included)

```
HORIZON SCANNING BRIEF — [DATE] — [PROFILE NAME]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TRIAGE SUMMARY
  🔴 Act Now:       N items
  🟠 Watch:         N items
  🟡 Monitor:       N items
  🟢 For Awareness: N items

TOP 5 ITEMS THIS PERIOD
  1. [Title] | Score: XX | Source: XX | Domains: XX
     [Annotation]
     [Suggested Action]
  ...

DOMAIN BREAKDOWN
  AI in Health:          XX items (top: ...)
  Digital Health & HIT:  XX items (top: ...)
  [Other active domains]
```

#### B. Full Item List

Each item rendered as:

```
──────────────────────────────────────────────────
[TRIAGE EMOJI] [TITLE]
Source: [SOURCE NAME] | Published: [DATE] | Horizon: H[N]
Score: [COMPOSITE]/100 — Evidence: [A] | Impact: [B] | Insurance: [C] | Relevance: [D]
Domains: [domain tags]

[SUMMARY / ABSTRACT EXCERPT]

Clinical note: [ANNOTATION]
Suggested action: [SUGGESTED ACTION]
URL: [URL]
──────────────────────────────────────────────────
```

#### C. Source Intelligence Map

A structured table of all active sources, showing: last scan date, items found, proportion in each triage tier, and whether the source is live/failing.

#### D. Trend Tracker (when historical data available)

Compare current period to previous period(s):
- New topics appearing for the first time
- Topics rising in score
- Topics that peaked and are declining
- Gaps: domains with no new activity

### 3.3 HTML Dashboard (interactive)

A self-contained HTML file (no server needed) with:

- **Triage kanban view**: columns for Act Now / Watch / Monitor
- **Domain filter**: click to show only ai_health or digital_health items
- **Score heatmap**: visual grid of items by evidence strength vs clinical impact
- **Source health panel**: green/amber/red status per source
- **Timeline chart**: items by published date (last 30/60/90 days toggle)

Generated from a Jinja2 template rendered to a single `.html` file. No external dependencies — chart.js bundled inline.

### 3.4 Trend Visualisation Data Model

Store each scan run in a lightweight SQLite database (`version2/data/scan_history.db`):

```sql
-- scan_runs: one row per run
CREATE TABLE scan_runs (
    id INTEGER PRIMARY KEY,
    run_id TEXT UNIQUE,          -- UUID
    profile TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    items_found INTEGER,
    items_scored INTEGER
);

-- scan_items: all items with scores
CREATE TABLE scan_items (
    id INTEGER PRIMARY KEY,
    run_id TEXT REFERENCES scan_runs(run_id),
    item_id TEXT,
    source_id TEXT,
    title TEXT,
    url TEXT,
    published_date DATE,
    domains TEXT,                -- JSON array
    composite_score REAL,
    triage_level TEXT,
    horizon_tier TEXT,
    annotation TEXT
);
```

This enables:
- Trend queries: "show items in ai_health that appeared for the first time this month"
- Score history: "has this source's output score changed over time"
- De-duplication across runs: "this item was already seen 14 days ago"

---

## Cross-Module: Configuration & Orchestration

### CLI interface (v2)

```bash
python -m v2.main scan \
  --profile phase1_ai_digital \
  --days 30 \
  --output ./version2/outputs/ \
  --format markdown html excel

python -m v2.main scan --profile full_scan --days 7

python -m v2.main report --from-db --period 90 --format html

python -m v2.main sources list               # show all sources with status
python -m v2.main sources test pubmed_eutils # test one source connection
```

### Configuration hierarchy

```
version2/
├── config/
│   ├── sources.yaml          # all 120+ sources
│   ├── domains.yaml          # keyword banks per domain
│   ├── scan_profiles.yaml    # named scan configurations
│   └── score_weights.yaml    # scoring dimension weights per profile
├── src/
│   ├── module1_scanner/
│   │   ├── __init__.py
│   │   ├── engine.py         # orchestrates all scanners
│   │   ├── scanners/
│   │   │   ├── api.py        # generic REST/JSON API scanner
│   │   │   ├── rss.py        # generic RSS/Atom scanner
│   │   │   ├── web.py        # generic web scraper
│   │   │   ├── pubmed.py     # PubMed-specific logic
│   │   │   ├── fda.py        # openFDA-specific logic
│   │   │   ├── nice.py       # NICE API-specific logic
│   │   │   ├── clinicaltrials.py
│   │   │   └── ema.py
│   │   ├── domain_tagger.py  # keyword matching engine
│   │   └── models.py         # ScanItem dataclass
│   ├── module2_scorer/
│   │   ├── __init__.py
│   │   ├── engine.py         # scoring orchestrator
│   │   ├── dimensions/
│   │   │   ├── evidence.py   # Dimension A
│   │   │   ├── impact.py     # Dimension B
│   │   │   ├── insurance.py  # Dimension C
│   │   │   └── relevance.py  # Dimension D
│   │   ├── annotator.py      # generates clinical annotations
│   │   └── models.py         # ScoreCard dataclass
│   ├── module3_reporter/
│   │   ├── __init__.py
│   │   ├── engine.py         # report orchestrator
│   │   ├── formatters/
│   │   │   ├── markdown.py
│   │   │   ├── html.py       # Jinja2 → self-contained HTML
│   │   │   ├── excel.py      # openpyxl
│   │   │   └── json_export.py
│   │   ├── templates/
│   │   │   ├── dashboard.html.j2
│   │   │   └── digest.md.j2
│   │   └── trend.py          # SQLite trend queries
│   ├── database.py           # SQLite ORM (scan_history.db)
│   ├── config_loader.py      # YAML config loading
│   └── main.py               # CLI entry point
├── data/
│   └── scan_history.db       # auto-created on first run
├── outputs/                  # generated reports
├── tests/
└── PLAN.md                   # this file
```

---

## Improvements Over Version 1

| Area | Version 1 | Version 2 |
|------|-----------|-----------|
| Source coverage | 30 sources | 120+ sources; Phase 1 AI/digital add-ons |
| Domain focus | 20 disease areas | Configurable domain profiles; Phase 1 = AI+digital |
| Scoring | Single composite (5 factors) | Four independent dimensions; per-profile weights |
| Insurance signal | Not modelled | Explicit dimension C |
| Trend analysis | Not available | SQLite history; trend queries |
| Visualisation | Markdown only | Markdown + self-contained HTML dashboard + Excel |
| Source database | Hardcoded in YAML | Full schema with programmatic access rating, horizon tier |
| Scan profiles | Single run | Named profiles (safety, AI/digital, full, insurance-focus) |
| Preprint handling | medRxiv only | medRxiv + bioRxiv with prominent peer-review flags |
| Configuration | `sources.yaml` + CLI flags | Three YAML files + named profiles |
| Output formats | Markdown + PDF | Markdown + HTML + Excel + JSON |

---

## Phased Rollout

| Phase | Scope | Deliverable |
|-------|-------|------------|
| **Phase 0** (now) | Planning, architecture, this document | `PLAN.md`, `TECH_STACK.md` |
| **Phase 1** | Module 1 + Module 2 for AI/digital health domains only | Working scanner + scorer for 20 Phase 1 sources |
| **Phase 2** | Module 3 reporting; full source library | HTML dashboard + Excel export; all 120+ sources active |
| **Phase 3** | History database; trend tracking; full scan profiles | Trend analysis; quarterly summary reports |
| **Phase 4** | Scheduling; alerting; email digests | Automated daily/weekly runs |
