# Canva / Claude Design prompt — Project HIDE presentation

Paste the prompt below into **Canva → Magic Design / "Design with Claude"**.
The deck is sized for a **10-minute talk with 3 speakers**, jury =
Professor Wided Guezguez and co-jurors. Live demo planned.

---

## Prompt to paste into Canva (Claude Design)

> Create a **12-slide presentation** for an academic project defence.
>
> **Subject:** *Project HIDE — Intelligent University Observatory: Research
> and Lab Management System using a Multi-Agent System.*
>
> **Audience:** academic jury (Professor Wided Guezguez and co-jurors).
>
> **Duration:** 10 minutes total, 3 speakers. ~50 seconds per slide on
> average.
>
> **Visual identity (must match — this is the project's product UI):**
>
> - Background: very dark `#0D1117`.
> - Card / surface: `#161B22` with a 1 px border `#30363D`.
> - Primary accent (titles, KPIs, links): electric blue `#2F81F7`.
> - Positive accent (metrics ↑, accepted): green `#3FB950`.
> - Warning accent (pending, attention): amber `#D29922`.
> - Danger accent (errors, rejected): red `#F85149`.
> - Text: `#E6EDF3` for primary, `#8B949E` for muted captions.
> - Typography: **IBM Plex Sans** for headings and body, **IBM Plex Mono**
>   for numbers, code, agent names, log lines.
> - Aesthetic: dense, scientific, mission-control, no rounded marketing
>   illustrations. Use subtle grids, thin lines, monochrome iconography
>   (lucide / phosphor outline style). No emoji, no gradients except a
>   hairline blue glow on KPI numbers.
>
> **Required slides (in this exact order, with the exact split between the
> 3 speakers shown in brackets):**
>
> **Slide 1 — Title slide [Speaker 1]**
> Big title: "Project HIDE". Subtitle: "Intelligent University Observatory
> — Research & Lab Management System using a Multi-Agent System".
> University, course and academic year placeholders. Three speaker names
> placeholders (split into a small row at the bottom). Date: May 2026.
> Background: dark with a subtle dotted grid; a single thin blue accent
> line under the title.
>
> **Slide 2 — Problem & objectives [Speaker 1]**
> Left column: 3 bullets describing the problem (fragmented research data,
> hard to find collaborations, no institutional analytics).
> Right column: 5 bullets listing project objectives in monospace
> shorthand: `MAS`, `clustering`, `expertise matching`, `Nash negotiation`,
> `web dashboard`. Show a small reference badge "Project_HIDE3.pdf §1–2".
>
> **Slide 3 — System architecture [Speaker 1]**
> Full-width architecture diagram with four horizontal layers (top to
> bottom): **Presentation** (React SPA · Flask REST API · Static assets),
> **Multi-Agent System (Mesa)** with eight named boxes (Coordinator;
> ResearcherScraper, PublicationScraper, LabScraper; Cluster,
> ExpertiseMatcher, CollabAdvisor, Negotiator), **Data layer** (seven
> SQLite tables in a row), **External** (Faker, Browser, mas.log,
> scikit-learn). Use the colour palette above to colour-code the agents:
> green = observers, blue = analysers, amber = negotiator, purple =
> coordinator. Thin vertical arrows between layers.
>
> **Slide 4 — Multi-Agent System: roles [Speaker 1 → hands off to Speaker 2]**
> Two-column table of the 7 step-driven agents. Columns: *Agent*,
> *Role*, *Output*. One row per agent. Use the IBM Plex Mono font for the
> agent names and keep each row to one line.
>
> **Slide 5 — Database schema (ER diagram) [Speaker 2]**
> Full-width ER diagram with the 7 tables: `labs`, `researchers`,
> `clusters`, `publications`, `researcher_publications`, `expertise`,
> `collaborations`. Show primary keys, foreign keys, and the
> relationships (`labs 1—N researchers`, `researchers N—M publications`
> via `researcher_publications`, `researchers 1—N expertise`,
> `researchers 2—N collaborations`). Caption: "7 tables, all FKs, indexes
> on lab_id and cluster_id."
>
> **Slide 6 — AI clustering (AgentCluster) [Speaker 2]**
> Left half: a stylised mock 2D scatter plot of researchers, coloured by
> cluster (use 6 distinct colours from the palette). Right half: a 3-line
> formula card showing the algorithm: KMeans with `k ∈ [2, 12]` selected
> by silhouette, DBSCAN as an alternative, winner = max(silhouette).
> Below: a tiny KPI strip showing "200 researchers · 18-dim features ·
> 8 clusters · σ = 0.10".
>
> **Slide 7 — Expertise matching + advisor [Speaker 2]**
> Left half: a 200×200 cosine-similarity heatmap mock (just a coloured
> grid). Right half: numbered pipeline TF-IDF → cosine sim → top-K → top-N
> recommended. Show the headline number "20 pairs recommended /
> 404 candidates" in the IBM Plex Mono font. Mention that `AgentCollabAdvisor`
> is the agent producing this top-N.
>
> **Slide 8 — Game-theoretic negotiation [Speaker 2 → hands off to Speaker 3]**
> Centrepiece: a 2×2 payoff-matrix card identical to the one in the live
> dashboard. Rows: A = Cooperate / Defect. Columns: B = Cooperate /
> Defect. Highlight the (C, C) cell with a green border and the label
> "◆ NASH". Below: a 3-stat row — `accept threshold = 0.15`, `pareto
> floor = 0.05`, `avg Nash = 0.24`.
>
> **Slide 9 — Web dashboard tour [Speaker 3]**
> 5-tile grid of dashboard screenshots, one tile per page (Overview,
> Researchers, Clusters, Collaborations, Agents). Each tile gets a
> mini-caption in monospace: e.g. `1 — Overview · 5 KPIs + 2 charts`.
> Add a small banner at the bottom: "Flask REST API · 16 endpoints · 4
> partial-rerun POSTs".
>
> **Slide 10 — Live demo placeholder [Speaker 3]**
> Big monospace title: `> live demo`. Three bullet points listing the
> demo script: (1) reset & reseed DB, (2) run full MAS cycle from the
> sidebar, (3) open Collaborations → payoff matrix and accept all
> pending. Subtle blinking-cursor style on the title.
>
> **Slide 11 — Spec compliance scoreboard [Speaker 3]**
> A scoreboard-style slide with 4 numbers, monospace, very large:
> `6/6` high-level requirements, `5/5` mandatory learning objectives
> (LLM is optional), `7/9` named agents implemented, `5/5` spec tables
> (delivered as a superset). Below the scoreboard: a one-line note in
> muted text: "Gaps: live scraping, dashboard-as-agent, optional LLM —
> see §11–12 of the report."
>
> **Slide 12 — Conclusion + Q&A [All three speakers, line up for questions]**
> Three short bullet conclusions:
> 1. Functional 7-agent MAS with Nash-driven negotiation.
> 2. Reproducible offline pipeline + dark mission-control dashboard.
> 3. Cleanly extensible: scraping, dashboard agent, LLM all isolated.
> A large monospace `> questions ?` at the bottom. Speaker names + emails
> in a small footer row.
>
> **Speaker notes:**
> Generate concise speaker notes (3–5 sentences each) in the slide
> footer area. Each set of notes must call out the key transition phrase
> the speaker should say to hand off to the next speaker (between slides
> 4 and 5, slides 8 and 9). Notes target ~50 seconds of speaking per
> slide.
>
> **Other constraints:**
> - Slide aspect ratio: 16:9.
> - Page numbers bottom-right, monospace, muted.
> - One small footer left-aligned: "Project HIDE · 2026 · supervisor:
>   Wided Guezguez".
> - No stock photos. Use only diagrams, mock charts, and screenshots.
> - Do not introduce colours outside the palette above.
> - Do not use emojis.

---

## Live-demo cheat-sheet (read this once before pasting the prompt)

The slide deck has a *demo placeholder* at slide 10 — during the talk,
switch to the browser at `http://localhost:5000` and run this exact
3-step script (≈ 90 seconds):

1. **Agents → Reset + reseed DB** → confirm. (Shows that the system
   bootstraps from zero.)
2. **Sidebar → Run MAS Cycle.** Let the spinner finish (~1 second).
   Switch to the **Agents** page so the live log auto-tails the
   8 agent lines.
3. **Collaborations** page → click on a pending row → hover the **payoff
   matrix** to point out the green Nash cell → click **Accept all
   pending**.

If the network is unreliable, fall back to slide 9 (5-tile dashboard
screenshot grid).

---

## How the 3 speakers split the deck

| Slides | Speaker | Focus |
|---|---|---|
| 1 – 4 | Speaker 1 | Context, objectives, architecture, MAS overview |
| 5 – 8 | Speaker 2 | DB schema, AI clustering, expertise matching, Nash negotiation |
| 9 – 12 | Speaker 3 | Dashboard tour, live demo, spec compliance, conclusion |

Total: ~3 minutes 20 seconds per speaker.

---

## Optional polish

After Canva generates the deck, ask Claude Design as a follow-up:

> "Tighten every bullet to 8 words or fewer. Replace any emoji or
> rounded-cartoon icons with thin outline icons in the style of *lucide*
> or *phosphor*. Make sure the IBM Plex Mono is used for every number,
> every agent name, every endpoint path, and every file path."

For the diagrams that Canva renders less well (architecture, ER), drop
in the four PNGs already produced by `python scripts/make_figures.py`
(in `figures/`) — they are sized at 6.4-inch width and ready to paste:

- `figures/fig1_architecture.png` → slide 3
- `figures/fig2_mas_sequence.png` → optional slide between 3 and 4
- `figures/fig3_er_diagram.png` → slide 5
- `figures/fig4_class_diagram.png` → optional, between 4 and 5
