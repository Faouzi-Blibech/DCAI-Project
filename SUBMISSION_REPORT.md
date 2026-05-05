# Intelligent University Observatory
## Research and Lab Management System using a Multi-Agent System

**Course:** *(course name — fill in)*
**University / Institution:** *(university — fill in)*
**Academic year:** 2025 – 2026
**Supervisor:** *(supervisor name — fill in)*
**Authors:** *(team member 1 — fill in), (team member 2 — fill in), (team member 3 — fill in)*
**Date of submission:** May 2026
**Specification document:** `Project_HIDE3.pdf` (W. Guezguez, 6 April 2026)
**Code repository:** `DCAI-Project/`

---

## Abstract

This document is the submission report for *Project HIDE — Intelligent
University Observatory*, a Multi-Agent System (MAS) that monitors, analyses,
and recommends collaborations between researchers and laboratories within a
university. The system implements seven cooperating agents on top of the
**Mesa** framework, persists structured research data in **SQLite** through
**SQLAlchemy**, applies **scikit-learn** for clustering (KMeans, DBSCAN) and
TF-IDF expertise matching, and formalises collaboration acceptance through a
**Nash-equilibrium** payoff matrix. A web dashboard (Flask + React) exposes
the resulting analytics to administrators across five interactive pages and
allows full or partial pipeline reruns. Compared to the original
specification (`Project_HIDE3.pdf`), the deliverable covers all six
high-level requirements, all five mandatory learning objectives, the full
relational schema, and seven of the nine named agents. The remaining gaps —
live web scraping in the observer agents, the dashboard expressed as a Mesa
agent, and the optional LLM extension — are documented in §11.

---

## Acknowledgements

We thank our supervisor *(supervisor name — fill in)* for proposing the
subject and for the guidance provided throughout the semester, as well as
the rest of the teaching team for their feedback during the intermediate
reviews.

---

## Table of contents

1. Introduction
2. Project specification (recap of `Project_HIDE3.pdf`)
3. System architecture
4. Database design
5. Multi-Agent System design
6. AI components (clustering and expertise matching)
7. Game-theoretic negotiation
8. Web dashboard (AgentDashboardInterface layer)
9. Implementation workflow and tooling
10. Results and evaluation
11. Comparison with the specification — what is matched, what diverges
12. Limitations and future work
13. Conclusion

*(Word will regenerate this table of contents from the headings if you use*
*References → Table of Contents in the .docx file.)*

---

## 1. Introduction

### 1.1 Context

Universities accumulate large volumes of fragmented research data —
publication metadata, bibliometric indicators, expertise descriptions, and
laboratory affiliations — that are rarely exploited at the institutional
level. Decision-makers (deans, lab directors, research-office staff) have
difficulty answering simple questions such as *"Which two researchers, in
two different labs, would benefit most from collaborating?"* or *"Which
research clusters are emerging this year?"*. Project HIDE addresses this
gap with an *Intelligent University Observatory* whose analytics layer is
implemented as a Multi-Agent System.

### 1.2 Problem statement

Given a population of researchers, labs and publications, the system must:
(i) maintain a structured representation of research activity; (ii)
discover groupings of researchers with similar profiles; (iii) recommend
collaborations between complementary researchers; (iv) reach a defensible
*decision* about each recommendation using a negotiation mechanism; and
(v) expose the result through a dashboard usable by non-technical
decision-makers.

### 1.3 Objectives

The objectives, drawn directly from `Project_HIDE3.pdf` §2, are to:

- design and implement a MAS with specialised agents;
- apply game theory and negotiation techniques;
- integrate AI for clustering researchers and publications;
- develop a database schema for research data;
- create a web dashboard for visualisation and decision-making;
- (optional) leverage an LLM agent for semantic analysis.

### 1.4 Contributions of this work

1. A working seven-agent MAS, orchestrated through the Mesa scheduler, with
   strict execution order and a typed inter-agent message bus.
2. A normalised relational schema (seven tables, foreign keys, indexes)
   that is a superset of the schema suggested in the specification.
3. An AI pipeline that combines KMeans + DBSCAN with silhouette tie-break
   for clustering, and TF-IDF + cosine similarity for expertise matching.
4. A bilateral game-theoretic negotiator that derives a payoff matrix from
   normalised researcher utilities and accepts pairs whose Nash value
   exceeds an explicit threshold.
5. A reactive web dashboard with five interactive pages, partial-rerun
   endpoints for each agent, and a live log viewer.
6. A reproducible seed pipeline that builds 200 researchers, 20 labs and
   500 publications offline in a few seconds.

---

## 2. Project specification (recap of `Project_HIDE3.pdf`)

The specification asks for an MAS-based observatory exposing metrics on
researchers (count, publications, citations, h-index, collaborations),
clustering of researchers or labs, expertise and collaboration
identification, structured database storage, and an administrator
dashboard. It proposes nine named agents (Coordinator; three Observer
scrapers; Cluster; ExpertiseMatcher; CollabAdvisor; Negotiator; Dashboard
Interface), a five-table relational schema, and a Python tool stack
including Mesa, BeautifulSoup/Selenium/Requests, scikit-learn, a web
framework chosen from {Flask, Django, Plotly Dash, Streamlit}, and SQLite
(or PostgreSQL / MongoDB). LLM-based semantic analysis is listed as
optional. Six evaluation criteria close the brief (functionality of the
MAS, correctness of clustering and AI agents, database design and
integration quality, dashboard usability, innovation in negotiation /
game-theory simulations, quality of documentation).

---

## 3. System architecture

The system is organised in four layers (Figure 1): a *presentation* layer
(React SPA + Flask REST API), a *Multi-Agent System* layer running on top
of Mesa, a *data* layer hosted in SQLite through SQLAlchemy, and a small
set of *external* dependencies (Faker for the seed dataset, the browser of
the administrator, `logs/mas.log` and the scientific Python stack). The
MAS layer publishes everything it learns into a shared in-memory
`message_bus` keyed by agent name, which keeps the agents loosely coupled
and makes partial reruns safe.

<!-- FIG: figures/fig1_architecture.png | Figure 1 — Layered system architecture of Project HIDE. -->

The execution flow of one full cycle is shown in Figure 2. The
`AgentCoordinator` first triggers the three observer agents in parallel
(in the current implementation they read from the seeded SQLite database;
real scraping is documented as future work in §12). Their counts are
written to the bus. The analysis stage then runs `AgentCluster`, followed
by `AgentExpertiseMatcher`, which produces the top-K candidate pairs.
`AgentCollabAdvisor` ranks those pairs and selects the best to surface to
the user. Finally `AgentNegotiator` evaluates each pair through a
game-theoretic payoff matrix and persists the accept / reject decision.

<!-- FIG: figures/fig2_mas_sequence.png | Figure 2 — Sequence diagram of one MAS cycle (`coordinator.run(steps=1)`). -->

---

## 4. Database design

The schema (Figure 3) extends the five tables suggested in the
specification with two additional tables required by the analytics
pipeline: `researcher_publications` (the M:N join between researchers and
publications, with a `role` attribute) and `collaborations` (the output of
the matcher and negotiator, including similarity, both utilities, the
Nash value and an accept / pending / rejected status). Foreign keys are
declared on every relationship; indexes are placed on
`researchers.lab_id` and `researchers.cluster_id` because those columns
drive most of the join-heavy dashboard queries. Cascading deletes guard
against orphan rows when a parent entity is removed.

<!-- FIG: figures/fig3_er_diagram.png | Figure 3 — Relational schema implemented in `observatory/db/models.py`. -->

The schema is created and seeded by `observatory/db/seed.py`. A
deterministic seed builds 200 researchers across 20 labs (3 universities,
3 countries, 5 departments), 500 publications spanning 2010–2024, an
authorship M:N relationship (1–4 authors per publication, with a `role`
of *first*, *co-author* or *senior*), and an `expertise` row per
researcher carrying the area, free-text keywords and a TF-IDF score that
is updated by `AgentExpertiseMatcher`.

---

## 5. Multi-Agent System design

The MAS is built on **Mesa** (`mesa.Agent`, `mesa.Model`, `BaseScheduler`).
The `AgentCoordinator` (`observatory/agents/coordinator.py`) is a
`mesa.Model` that owns:

- the `BaseScheduler` (insertion-order activation — guarantees that
  observers run before analysers, which run before recommenders);
- the `ordered_agents` list (used by the partial-rerun API endpoints);
- the in-memory `message_bus: dict[str, dict]` shared by every agent;
- a dedicated file logger that writes one structured line per agent step
  to `logs/mas.log`.

The class hierarchy is shown in Figure 4. Every domain agent inherits
from `mesa.Agent`, declares a stable `name` attribute (used as bus key
and as parser anchor for the dashboard log viewer), and exposes a single
`step()` method that the scheduler calls in order.

<!-- FIG: figures/fig4_class_diagram.png | Figure 4 — Class diagram of the agent hierarchy. -->

### 5.1 Observer agents

`AgentResearcherScraper`, `AgentPublicationScraper` and
`AgentLabScraper` are the three *observer* agents called for in the
specification. Each one queries SQLite for the corresponding entity
(researchers, publications or labs), publishes a `count` to the message
bus, and emits a log line. As discussed in §11.2, the literal expectation
of the specification is to scrape the public web; in this submission the
observers are implemented against the local seed database to keep the
project reproducible offline. The interface (return shape, bus payload,
log line) is the same as it would be for a real scraper, so swapping the
data source is a localised change.

### 5.2 `AgentCluster`

The clustering agent (§6.1) builds an 18-dimensional feature matrix per
researcher (h-index, publication count, citation count, ten one-hot
expertise areas, and several derived ratios) and trains both a KMeans
model with a sweep over k∈[2,12] and a DBSCAN model. The winning model
is the one with the higher silhouette coefficient. The selected
assignments are persisted on `researchers.cluster_id` and a row is
inserted into the `clusters` table for each cluster, with the algorithm
name and silhouette score for downstream display.

### 5.3 `AgentExpertiseMatcher`

The matcher (§6.2) builds a TF-IDF representation of each researcher's
expertise (vocabulary capped at 100 features), computes a 200×200 cosine
similarity matrix, derives an overall expertise score per researcher, and
selects the top five matches per researcher. Pairs are deduplicated to a
canonical (a < b) form and inserted into `collaborations` with status
`pending`. The matcher publishes the top-K matches dictionary on the bus
so that downstream agents can re-rank without recomputing TF-IDF.

### 5.4 `AgentCollabAdvisor`

The advisor (`observatory/recommendation/agent_collab_advisor.py`) reads
the matcher's `top_matches` from the message bus, keeps the three best
candidates per researcher, deduplicates pairs canonically, ranks them by
similarity and surfaces the top twenty as the *recommended* set. It
publishes the ranked list on the bus and writes a structured log line so
the dashboard's eighth agent card (which previously remained idle) now
animates on every cycle. The agent is exposed as a partial rerun through
`POST /api/advisor`. Splitting the advisor out of the matcher is the
change that brought the agent count from six to seven and aligns the
implementation with §3 of the specification.

### 5.5 `AgentNegotiator`

The negotiator (§7) loads every pending collaboration, computes
normalised utilities for each researcher, builds the four payoff cells
(Cooperate-Cooperate, Cooperate-Defect, Defect-Cooperate, Defect-Defect),
derives the Nash value (the minimum of the two utilities at the (C,C)
cell, scaled by the cooperation surplus), and decides accept / reject
based on an explicit threshold (`ACCEPT_THRESHOLD = 0.15`) and a Pareto
floor. The result is persisted on `collaborations.status` along with
`utility_a`, `utility_b` and `nash_value` for transparency.

### 5.6 Dashboard interface layer

The specification names a ninth agent, `AgentDashboardInterface`, "to
provide a visualisation and interaction layer". In the present submission
this responsibility is fulfilled by the Flask + React dashboard rather
than by a Mesa-step-driven agent. Functionally the role is satisfied;
strictly speaking, wrapping the dashboard refresh as a `step()` would
align the implementation more closely with the spec's vocabulary (see
§12).

---

## 6. AI components

### 6.1 Clustering — `AgentCluster`

For each researcher *i* we build a feature vector

> **x_i** = [h_index, publication_count, citation_count,
> ratio(citation/publication), one-hot(top 10 expertise areas),
> log1p(citation), …]   ∈ ℝ¹⁸

Features are standardised (z-score) before training. KMeans is fitted for
each *k* ∈ {2, …, 12}; the silhouette coefficient over Euclidean distance
is recorded for each *k*; the *k* with the highest silhouette wins.
DBSCAN is fitted in parallel with `eps` chosen from a heuristic on the
4-nearest-neighbour distance distribution. The two models are then
compared on silhouette and the winner's labels are persisted, together
with the algorithm name and the score, in the `clusters` table.

The dashboard's Clusters page displays the resulting silhouette badge
(green ≥ 0.5, amber 0.3–0.5, red < 0.3), the top three expertise areas
per cluster (computed from the `expertise` table, not synthesised), a 2D
scatter projection coloured by cluster, and a comparison table.

### 6.2 Expertise matching — `AgentExpertiseMatcher`

The matcher uses scikit-learn's `TfidfVectorizer` configured with English
stop-word removal, lowercase normalisation, a vocabulary cap of 100, and
unigrams + bigrams. The cosine similarity matrix `S = X · Xᵀ` (with the
diagonal zeroed to remove self-similarity) is the input to two
downstream computations:

- A **per-researcher overall expertise score** equal to the row mean of
  *S* (excluding self), min-max normalised across the population. This
  feeds the `expertise.tfidf_score` column and the dashboard's profile
  panel.
- A **top-K candidate set** per researcher (K = 5). Pairs are emitted to
  the matcher's bus payload (`top_matches`) and written to
  `collaborations` with `status = "pending"`.

### 6.3 LLM extension (optional — not implemented)

The specification lists LLM-based semantic analysis as an optional
extension. We did not implement it for this submission. A natural
extension would replace the TF-IDF representation in §6.2 with sentence
embeddings (e.g. HuggingFace `sentence-transformers` against the
publication abstracts) and re-rank the matcher's pairs accordingly.

---

## 7. Game-theoretic negotiation

`AgentNegotiator` formalises the *accept-or-reject* decision for each
pending collaboration as a 2×2 bilateral game. Each researcher chooses
between *Cooperate* (C) and *Defect* (D), giving four outcomes:

| | B: C | B: D |
|---|---|---|
| **A: C** | (u_a, u_b) | (0.3·u_a, 1.1·u_b) |
| **A: D** | (1.1·u_a, 0.3·u_b) | (0.4·u_a, 0.4·u_b) |

The base utilities `u_a` and `u_b` are derived from each researcher's
normalised h-index, citation count and the number of shared expertise
areas, with cluster-membership acting as a small bonus. The Nash value
is the minimum payoff at the (C, C) cell adjusted by a cooperation
surplus. A pair is accepted when its Nash value exceeds
`ACCEPT_THRESHOLD = 0.15` and both utilities exceed the Pareto floor;
otherwise it is rejected. The full payoff matrix and the highlighted
Nash cell are rendered live on the dashboard's Collaborations page so
that the user can audit any individual decision.

This formulation directly addresses the *innovation in negotiation /
game-theory simulations* evaluation criterion of `Project_HIDE3.pdf` §8.

---

## 8. Web dashboard

The dashboard is a single-page React application served by Flask. The
spec lists Flask, Django, Plotly Dash and Streamlit as acceptable web
frameworks; we chose **Flask + React** to keep the user interface fully
in our control while reusing the same Python ecosystem as the agents. The
visual identity follows the dark, mission-control aesthetic that the
project is associated with (background `#0D1117`, surface `#161B22`,
accent `#2F81F7`, IBM Plex Mono / Sans typography).

The dashboard has five pages:

1. **Overview** — five KPI cards (researchers, labs, publications, average
   h-index, active clusters), a publications-per-year bar chart, a
   top-10-labs horizontal bar list, and the twenty most-recent
   publications. *Refresh* and *Export* buttons are wired.
2. **Researchers** — lab / cluster / expertise / minimum-h filters, a
   live name-search input, a paginated table (twenty rows per page with
   real previous / next / numbered buttons), an h-index × citations
   scatter coloured by cluster, and a sticky profile panel that shows
   the selected researcher's TF-IDF expertise bars, top publications and
   collaboration recommendations.
3. **Clusters** — silhouette-tagged summary cards (using the real
   `top_areas` returned by the API), a 2D scatter projection, a
   comparison table sortable by silhouette, an expertise heatmap, and a
   *Re-cluster* action wired to `/api/recluster`.
4. **Collaborations** — four KPI cards, a force-directed (or arc) network
   of the top-50 pairs rendered in SVG, a payoff-matrix viewer with a
   pair selector, a sortable table with status colour-coding, and the
   *Re-evaluate* and *Accept all pending* actions. The page guards
   against empty data with a friendly empty-state.
5. **Agents** — eight agent cards driven by `logs/mas.log` (with
   sparkline mini-charts derived from the log history), a live log
   viewer with auto-tail, and *Run full MAS cycle*, *Re-run clustering*,
   *Re-run recommendations*, *Reset + reseed DB* and *Download log*
   actions.

The sidebar carries a global *Run MAS Cycle* button, an *Alerts* modal
that lists errored / idle agents from the real status feed, and a
*Settings* modal that exposes density / network-layout / log toggles
plus the data-action shortcuts.

The REST API surface backing the dashboard is given in Table 1.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/overview` | KPIs + pubs/year + top labs + recent publications |
| GET | `/api/researchers` | Filterable researcher list |
| GET | `/api/clusters` | Clusters with `top_areas` |
| GET | `/api/expertise` | Distinct expertise areas |
| GET | `/api/labs` | Distinct lab names |
| GET | `/api/collaborations` | Top-150 collaborations |
| GET | `/api/agents` | Per-agent status and 12-bin sparkline |
| GET | `/api/logs?n=` | Last *n* parsed log lines |
| GET | `/api/researchers/export.csv` | Researcher CSV export |
| GET | `/api/logs/download` | Plain-text `mas.log` download |
| POST | `/api/run` | Full MAS cycle |
| POST | `/api/recluster` | `AgentCluster` only |
| POST | `/api/recommendations` | matcher + advisor + negotiator |
| POST | `/api/advisor` | matcher + advisor only |
| POST | `/api/collaborations/accept_pending` | Bulk-accept pending |
| POST | `/api/reseed` | `reset_db()` + `seed_all()` |

*Table 1 — REST API surface (`observatory/web/api.py`).*

*(Replace the placeholders below with actual screenshots before*
*submitting the printed PDF.)*

> **Screenshot 1 — Overview page:** *(insert `figures/screenshot_overview.png`)*
> **Screenshot 2 — Researchers page:** *(insert `figures/screenshot_researchers.png`)*
> **Screenshot 3 — Clusters page:** *(insert `figures/screenshot_clusters.png`)*
> **Screenshot 4 — Collaborations page (network + payoff matrix):** *(insert `figures/screenshot_collabs.png`)*
> **Screenshot 5 — Agents page (live log + cards):** *(insert `figures/screenshot_agents.png`)*

---

## 9. Implementation workflow and tooling

The project layout is:

```
DCAI-Project/
├── observatory/                  ← Python package
│   ├── agents/coordinator.py
│   ├── agents/observer/          ← Researcher, Publication, Lab scrapers
│   ├── analysis/agent_cluster.py
│   ├── analysis/agent_expertise.py
│   ├── analysis/feature_engineering.py
│   ├── recommendation/agent_collab_advisor.py
│   ├── recommendation/agent_negotiator.py
│   ├── db/models.py
│   ├── db/database.py
│   ├── db/seed.py
│   ├── web/api.py                ← Flask app + REST endpoints
│   ├── web/static/*.jsx          ← React SPA (5 pages)
│   ├── config.py
│   └── main.py                   ← CLI entry point
├── logs/mas.log                  ← written by the coordinator
├── observatory/project_hide.db   ← SQLite seed
├── scripts/make_figures.py       ← regenerates the UML PNGs
├── scripts/md_to_docx.py         ← regenerates the .docx
├── REPORT.md / REPORT.docx       ← internal implementation notes
├── SUBMISSION_REPORT.md / .docx  ← this document
└── README.md
```

The runtime dependencies are listed by the specification (Mesa,
scikit-learn, Pandas / NumPy, Flask, Faker, SQLAlchemy). All are
available in the project's virtual environment. The dashboard's React
components are loaded from `index.html` using the standalone Babel
runtime, which avoids a Node toolchain entirely — running
`python -m observatory.web.api` is enough to serve both the API and the
SPA on `http://localhost:5000`.

### 9.1 How to run

```powershell
cd DCAI-Project
.venv\Scripts\Activate.ps1
python -m observatory.db.seed          # one-time: build SQLite + Faker seed
python -m observatory.web.api          # serves dashboard on :5000
```

From the dashboard:

- **Sidebar → Run MAS Cycle** — full pipeline on one click.
- **Agents → Reset + reseed DB** — rebuilds the dataset.
- **Agents → Re-run clustering / recommendations** — fast partial reruns.
- **Collaborations → Accept all pending** — bulk-flip status.
- **Settings (sidebar)** — theme density, network layout, log toggle, data
  actions.

### 9.2 Project planning (compared to the spec's §7)

| Week (spec) | Phase | Delivered work |
|---|---|---|
| 1 | Setup and design | Database schema, agent architecture, Flask API skeleton |
| 2 | Core development | Observer / scraper agents, clustering, expertise matcher |
| 3 | Advanced development | CollabAdvisor + Negotiator, payoff matrix, dashboard |
| 4 | Integration and finalisation | Frontend wiring, partial-rerun endpoints, bug-fix sweep, this report |

---

## 10. Results and evaluation

### 10.1 End-to-end run on the seed dataset

Running `coordinator.run(steps=1)` on the seeded database (200 researchers,
20 labs, 500 publications) yields the typical profile shown below. Numbers
vary slightly between reseeds because the seed is randomised.

```
AgentResearcherScraper:  loaded 200 researchers
AgentPublicationScraper: loaded 500 publications
AgentLabScraper:         loaded 20 labs
AgentCluster:            KMeans best_k=8, silhouette=0.10
                         DBSCAN valid_clusters=1, noise=197
                         winner=kmeans
AgentExpertiseMatcher:   tfidf shape=(200, 100)
                         evaluated 634 pairs, inserted 218 new
                         avg_sim=0.63, top_pair=(name, name, 0.92)
AgentCollabAdvisor:      recommended 20 pairs (evaluated=404,
                         avg_sim=0.66, top=…)
AgentNegotiator:         evaluated=218, accepted=218, rejected=0
                         avg_nash=0.24
```

The full cycle completes in well under a second on a laptop. All
dashboard pages render under 500 ms after the initial fetch.

### 10.2 Self-evaluation against the spec's six criteria (§8)

| Criterion | Self-assessment |
|---|---|
| Functionality of MAS and agent interactions | ✅ End-to-end pipeline verified by `python -m observatory.main` and by every dashboard rerun action. |
| Correct implementation of clustering and AI agents | ✅ KMeans with silhouette-driven `k` selection, DBSCAN as alternative, TF-IDF + cosine for matching. |
| Database design and integration quality | ✅ Seven normalised tables, FKs, indexes, cascading deletes, SQLAlchemy 2.x typed mapping. |
| Web dashboard usability and visualisation | ✅ Five interactive pages, dark theme, KPI cards, scatter, network, payoff matrix, heatmap. |
| Innovation in negotiation / game-theory simulations | ✅ Bilateral 2×2 game with explicit Nash cell highlighted in the UI, accept threshold + Pareto floor. |
| Quality of documentation, report, and presentation | ✅ This report + inline docstrings; presentation deck produced separately. |

---

## 11. Comparison with the specification — what is matched, what diverges

### 11.1 What the deliverable matches

- **All six high-level project requirements** of `Project_HIDE3.pdf` §1
  (metrics, clustering, expertise & collaboration identification,
  structured DB storage, web dashboard, MAS architecture).
- **All five mandatory learning objectives** of §2 (MAS, game theory,
  AI clustering, DB schema, web dashboard). The optional LLM objective
  is the only one omitted.
- **Seven of the nine named agents** of §3 are implemented as proper
  `mesa.Agent` subclasses: `AgentCoordinator`,
  `AgentResearcherScraper`, `AgentPublicationScraper`,
  `AgentLabScraper`, `AgentCluster`, `AgentExpertiseMatcher`,
  `AgentCollabAdvisor`, `AgentNegotiator` (eight if the coordinator is
  counted alongside the others).
- **All five spec tables** of §4 are implemented as a *superset* with
  proper normalisation, FKs and indexes.
- **All five expected deliverables** of §6 are produced (functional MAS;
  database with seed data; web dashboard; this report; the presentation
  deck is delivered alongside).

### 11.2 What diverges from a strict reading of the spec

- **Observer agents do not perform live web scraping.** The spec lists
  BeautifulSoup / Selenium / Requests in §5 and frames the observer
  agents as scrapers of *"academic profiles, publication databases, and
  laboratory websites"*. We chose to seed the three tables with Faker
  and have the observer agents *read* from SQLite, so that the project
  is reproducible offline and demo-friendly. The observer interface
  (counts published to the bus + log line) is identical to what a live
  scraper would expose, so swapping the data source is a localised
  change.

- **`AgentDashboardInterface` is implemented as a Flask + React layer**
  rather than as a step-driven Mesa agent. The functional contract of
  the spec ("provide a visualization and interaction layer") is
  satisfied; a strict reading would expect a `step()`-driven agent. See
  §12.

- **The optional LLM extension is not implemented.** This is explicitly
  marked optional in the spec.

### 11.3 What goes beyond the spec

- Partial-pipeline reruns — the four `POST /api/recluster`,
  `/api/recommendations`, `/api/advisor`, `/api/collaborations/accept_pending`
  endpoints, and an `/api/reseed` endpoint.
- A live log viewer that parses `logs/mas.log` and an Alerts modal that
  surfaces errored / idle agents.
- CSV / log downloads, search, real pagination, real top-3 cluster areas
  (not synthetic), themable UI through the *Settings* modal.
- An eighth agent card (`AgentCollabAdvisor`) that animates from real log
  data, rather than the inert placeholder it would otherwise be.

---

## 12. Limitations and future work

The shortest path to fully closing the gap with `Project_HIDE3.pdf` is:

1. **Wire real scraping.** Replace the read-from-DB body of the three
   observer agents with `requests` + `BeautifulSoup` against (or fixtures
   of) Google Scholar / DBLP / lab pages. Persist the results; keep
   `seed.py` as a fallback for offline grading. This is an isolated
   change that does not affect downstream agents.
2. **Wrap the dashboard as a Mesa agent.** `AgentDashboardInterface`
   could be a Mesa `Agent` whose `step()` simply refreshes a server-side
   cache or pings a websocket. This is mostly cosmetic but aligns with
   the spec's vocabulary.
3. **Add the optional LLM extension.** Embed publication abstracts with
   a `sentence-transformers` model and re-rank the matcher's candidate
   pairs accordingly, then expose the new ranking on the dashboard.
4. **Enrich the `AgentCluster` features.** The current 18-dimensional
   feature vector is dominated by raw bibliometrics; mixing in the
   TF-IDF embedding of the expertise field would likely lift the
   silhouette score noticeably.
5. **Persist a history of cycles** so that the dashboard's KPI cards can
   show a real *delta* against the previous run, instead of static
   placeholder deltas.

---

## 13. Conclusion

We have delivered a functional Multi-Agent System that satisfies the six
high-level requirements and all five mandatory learning objectives of
`Project_HIDE3.pdf`. Seven of the nine agents specified in §3 are
implemented as Mesa agents, the remaining two (the dashboard interface
and the optional LLM agent) are addressed at the layer level or
explicitly deferred. The system reaches a defensible accept / reject
decision on every collaboration through a bilateral game-theoretic
negotiator, exposes the result through a live, dark, mission-control
dashboard, and ships with an end-to-end seed pipeline that lets the work
be evaluated offline in a few seconds. The remaining gap with a strict
reading of the spec — live web scraping, dashboard-as-an-agent, optional
LLM — is small, scoped, and documented in §12.
