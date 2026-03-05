# PPFAS Mutual Fund FAQ Assistant

A Retrieval-Augmented Generation (RAG) chatbot that answers factual questions about PPFAS Mutual Fund schemes. Data is sourced exclusively from official Groww scheme pages, embedded locally with `all-MiniLM-L6-v2`, and served through a constrained Google Gemini prompt. A GitHub Actions workflow re-scrapes, re-indexes, and redeploys the app each day.

> **Scope:** This assistant covers PPFAS Mutual Fund only (7 direct-growth schemes). It answers factual queries — expense ratio, exit load, minimum SIP, lock-in, riskometer, benchmark — and does not offer investment advice.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Tech Stack](#tech-stack)
- [Scheme Coverage](#scheme-coverage)
- [Prerequisites](#prerequisites)
- [Quickstart](#quickstart)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Automated Data Refresh (CI/CD)](#automated-data-refresh-cicd)
- [Deploying to Render](#deploying-to-render)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## How It Works

```
User query
    │
    ├─► Guardrail layer (Phase 3)
    │       PII check   →  blocks PAN, Aadhaar, phone, email, bank account numbers
    │       Intent check →  blocks advisory queries ("should I invest…", "best fund for…")
    │
    ├─► RAG pipeline (Phase 4)
    │       1. Embed query with all-MiniLM-L6-v2
    │       2. FAISS similarity search → top-3 atomic factual chunks
    │       3. Gemini API generation (≤3 sentences, strictly from context)
    │       4. Append source URL + last_updated timestamp
    │
    └─► FastAPI backend + Vanilla HTML/JS frontend (Phase 5)

────────────────────────────────────────────────
Data pipeline  (GitHub Actions, daily 00:00 UTC)

Phase 1  Playwright scraper  →  ppfas_schemes.json
Phase 2  Indexer             →  FAISS index + metadata pickle
Phase 6  Scheduler           →  orchestrates Phases 1–2 + full test suite
```

The scraper uses a headless Chromium browser (via Playwright) to handle Groww's client-rendered React pages. Field extraction combines BeautifulSoup selector traversal with JavaScript DOM evaluation injected directly into the live page.

Every answer carries the exact Groww source URL and the `last_updated` timestamp from the scraped record. Answers without a matching context chunk are surfaced as "I cannot find this information in the official source."

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Scraping | Playwright + BeautifulSoup4 | 1.49.1 / 4.13.3 |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | 3.4.1 |
| Vector store | FAISS CPU (`IndexFlatIP`) + Pickle | 1.9.0 |
| LLM | Google Gemini API (`google-genai`) | 1.3.0 |
| Backend | FastAPI + Uvicorn | 0.115.8 / 0.34.0 |
| Frontend | Vanilla HTML / CSS / JavaScript | — |
| Testing | Pytest | — |
| CI/CD | GitHub Actions + Render | — |

**Operating cost: $0.** All core components run on Google Gemini's free tier, open-source embeddings, and local FAISS.

---

## Scheme Coverage

**AMC:** PPFAS Mutual Fund  
**Source:** `https://groww.in/mutual-funds/amc/ppfas-mutual-funds`

| Scheme | Category |
|---|---|
| Parag Parikh Long Term Value Fund – Direct Growth | Equity (Flexi Cap) |
| Parag Parikh ELSS Tax Saver Fund – Direct Growth | ELSS (Tax Saver) |
| Parag Parikh Conservative Hybrid Fund – Direct Growth | Hybrid |
| Parag Parikh Liquid Fund – Direct Growth | Liquid |
| Parag Parikh Arbitrage Fund – Direct Growth | Arbitrage |
| Parag Parikh Dynamic Asset Allocation Fund – Direct Growth | Dynamic Asset Allocation |
| Parag Parikh Large Cap Fund – Direct Growth | Large Cap |

**Fields captured per scheme:** `scheme_id`, `scheme_name`, `amc_name`, `fund_category`, `expense_ratio`, `minimum_sip`, `minimum_lumpsum`, `exit_load`, `lock_in_period`, `riskometer_category`, `benchmark_index`, `source_url`, `last_updated`.

Only direct-growth variants of these 7 schemes are in scope. No third-party data sources are used.

---

## Prerequisites

- Python 3.12
- A Google Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com)
- Git

---

## Quickstart

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Create a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Playwright browser

```bash
playwright install chromium
```

### 5. Set your API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_api_key_here
```

The `.env` file is gitignored and never committed.

### 6. Build the data pipeline

This scrapes Groww, validates the output, builds the FAISS index, and runs the full test suite. The pipeline aborts at the first failure.

```bash
python phase6_scheduler/scheduler.py
```

Pipeline steps in order:

| Step | What it does |
|---|---|
| Phase 1 — Scraper | Crawls 7 Groww scheme pages with headless Chromium |
| Data integrity check | `pytest tests/test_scraper.py` — validates JSON schema and mandatory fields |
| Phase 2 — Indexer | Chunks facts, embeds with MiniLM, writes FAISS index + metadata pickle |
| Vector store check | `pytest tests/test_indexer.py` — validates index dimensions and chunk count |
| Regression tests | `pytest tests/test_guardrails.py tests/test_api.py` |

### 7. Start the server

```bash
cd phase5_ui
uvicorn api:app --host 0.0.0.0 --port 8000
```

The frontend is served at the root `/`. The API is available at `POST /api/chat`.

**Example request:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the exit load of the Liquid Fund?"}'
```

**Example response:**

```json
{
  "answer": "The Parag Parikh Liquid Fund – Direct Growth has an exit load of Nil.",
  "sources": ["https://groww.in/mutual-funds/parag-parikh-liquid-fund-direct-growth"],
  "last_updated": "2025-03-05 05:30:01"
}
```

---

## Project Structure

```
.
├── phase1_ingestion/
│   ├── scraper.py              # Playwright + BS4 scraper with JS DOM injection
│   ├── schema.py               # Pydantic model for extracted scheme data
│   └── data/structured/        # ppfas_schemes.json (output, committed)
│
├── phase2_indexing/
│   ├── indexer.py              # Chunking → MiniLM embeddings → FAISS write
│   └── faiss_db/               # ppfas_index.faiss + ppfas_metadata.pkl
│
├── phase3_guardrails/
│   └── controller.py           # Regex-based PII and advisory intent filter
│
├── phase4_rag/
│   └── rag_engine.py           # End-to-end RAG: guardrail → retrieve → generate → cite
│
├── phase5_ui/
│   ├── api.py                  # FastAPI app: POST /api/chat + static file mount
│   └── static/                 # Vanilla HTML/CSS/JS frontend
│
├── phase6_scheduler/
│   └── scheduler.py            # Pipeline orchestrator (subprocess, sequential)
│
├── tests/
│   ├── test_scraper.py         # Schema and mandatory field validation
│   ├── test_indexer.py         # FAISS index and metadata integrity
│   ├── test_guardrails.py      # PII and advisory blocking assertions
│   └── test_api.py             # FastAPI endpoint response tests
│
├── .github/workflows/
│   └── scheduler.yml           # Daily cron job (00:00 UTC) + manual dispatch
│
├── architecture.md             # Detailed phase-by-phase design document
└── requirements.txt
```

---

## Configuration

| Variable | Location | Description |
|---|---|---|
| `GEMINI_API_KEY` | `.env` file (local) / GitHub Secret / Render env var | Google Gemini API key |
| `RENDER_DEPLOY_HOOK_URL` | GitHub Secret (optional) | Render deploy hook; if absent, the CI step is skipped |
| `PORT` | Set automatically by Render | Uvicorn binds to this port in production |

The RAG engine falls back through `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-2.5-flash-lite` if a quota error (HTTP 429) is encountered.

---

## Running Tests

```bash
# Full test suite
pytest tests/ -v

# Individual files
pytest tests/test_scraper.py -v      # Scraped JSON schema and field coverage
pytest tests/test_indexer.py -v      # FAISS index dimensions and chunk count
pytest tests/test_guardrails.py -v   # PII and advisory query blocking
pytest tests/test_api.py -v          # FastAPI /api/chat endpoint contracts
```

---

## Automated Data Refresh (CI/CD)

The workflow at `.github/workflows/scheduler.yml` runs at **00:00 UTC (5:30 AM IST) daily** and can be triggered manually from the Actions tab.

**Workflow steps:**

1. Check out repository
2. Set up Python 3.12 with pip cache
3. Install dependencies and Playwright Chromium
4. Run `phase6_scheduler/scheduler.py` (full pipeline + tests)
5. Auto-commit changed data files back to the repository:
   - `data/raw/*.html`
   - `data/structured/*.json`
   - `data/vector_store/*.index`
   - `data/vector_store/*.pkl`
6. Trigger a Render redeploy via deploy hook (if secret is configured)

**Required GitHub Secrets:**

| Secret | Required | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | Yes | Gemini API calls during test_api.py regression |
| `RENDER_DEPLOY_HOOK_URL` | No | Triggers Render redeploy after a successful pipeline run |

---

## Deploying to Render

The `api.py` entrypoint reads the `PORT` environment variable and binds to `0.0.0.0`, which is compatible with Render's web service runtime.

**Recommended Render settings:**

| Setting | Value |
|---|---|
| Environment | Python 3 |
| Build Command | `pip install -r requirements.txt && playwright install chromium` |
| Start Command | `cd phase5_ui && uvicorn api:app --host 0.0.0.0 --port $PORT` |
| Environment Variable | `GEMINI_API_KEY` = your key |

The GitHub Actions workflow commits refreshed data files (JSON, FAISS index, pickle) directly to the repository on each daily run. Each Render redeploy then picks up the latest data without needing to run the scraper on Render itself.

---

## Known Limitations

| Limitation | Detail |
|---|---|
| Single AMC | Covers PPFAS Mutual Fund only. Adding other AMCs requires new seed URLs and a pipeline re-run. |
| Groww DOM dependency | The Playwright scraper targets specific DOM structures on Groww. A site redesign will require scraper updates. |
| No NAV or returns data | Captures only static fund attributes. Does not track NAV, historical returns, or portfolio holdings. |
| Direct Growth variants only | Regular plan URLs are outside scope. |
| File-based vector store | FAISS index is stored as committed files. Suitable for a small, fixed scheme set; does not scale horizontally. |
| Regex-based guardrails | Advisory intent detection uses heuristic patterns. Sophisticated paraphrasing may bypass the filter. |
| Gemini free-tier rate limits | Three model fallbacks are implemented, but sustained concurrent traffic can exhaust all tiers. |

---

## License

This project is for portfolio and educational demonstration purposes. It is not affiliated with PPFAS Mutual Fund, Groww, or Google.
