# SolRise — AI-Powered SEO & GEO Marketing Platform

> IE University Capstone Project · April 2026

SolRise is a full-stack AI marketing platform that analyses websites for **SEO** (Google search visibility) and **GEO** (Generative Engine Optimisation — being cited by ChatGPT, Perplexity, Gemini, Claude, and Google AI Overviews). It generates branded PDF reports, identifies competitor gaps, and can build or optimise a client's website using the analysis results.

**Live demo:** [solrise.netlify.app](https://beamish-ganache-002aac.netlify.app)

---

## What It Does

- Scrapes and analyses any website for SEO and GEO readiness
- Benchmarks performance against up to 3 competitors
- Identifies keyword gaps and content opportunities
- Generates a branded PDF report with scores and recommendations
- Builds or optimises a website using LLM-generated, schema-rich content
- Stores all projects and results in MongoDB for repeat access

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + Vite, Recharts, Framer Motion |
| Backend | Python 3, Flask, Flask-CORS |
| Database | MongoDB |
| NLP / ML | spaCy, scikit-learn (TF-IDF), sentence-transformers |
| Web Scraping | BeautifulSoup4, Crawl4ai |
| AI / LLM | Ollama (llama3.2, local) + Anthropic Claude API |
| PDF Reports | ReportLab + Matplotlib |
| Deployment | Netlify (frontend) |

---

## Project Structure

```
solrise/
├── frontend/               # React + Vite SPA
│   ├── src/
│   │   ├── solrise/        # Public-facing marketing site
│   │   │   ├── pages/      # HomePage, ServicesPage, AboutPage, QuizPage
│   │   │   └── components/ # Header, Footer, SunLogo
│   │   └── dashboard/      # Internal analysis tool
│   │       ├── AnalyzePanel.jsx
│   │       ├── ResultsPanel.jsx
│   │       ├── GeneratePanel.jsx
│   │       └── ValidationPanel.jsx
│   ├── public/
│   │   └── _redirects      # Netlify SPA routing
│   └── vercel.json         # Vercel SPA routing
│
├── backend/
│   ├── app.py                       # Flask API (main entry point)
│   ├── pipeline.py                  # Pipeline interface
│   ├── pipelines/
│   │   └── pipeline_v8.py           # Core SEO/GEO analysis pipeline
│   ├── solrise_report_generator.py  # PDF report builder
│   └── requirements.txt
│
└── setup.sh                # Automated setup script
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+
- [MongoDB](https://www.mongodb.com/try/download/community) running on port 27017
- [Ollama](https://ollama.ai) running with `llama3.2` model

### Automated Setup

```bash
bash setup.sh
```

### Manual Setup

**1. Backend**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m spacy download en_core_web_sm
```

Create a `.env` file in `backend/`:
```
MONGO_URI=mongodb://127.0.0.1:27017/solrise
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**2. Frontend**
```bash
cd frontend
npm install
```

### Running Locally

```bash
# Terminal 1 — MongoDB
mongod --dbpath /tmp/mongodb-data

# Terminal 2 — Ollama
ollama serve && ollama pull llama3.2

# Terminal 3 — Backend (port 5001)
cd backend && source .venv/bin/activate && python app.py

# Terminal 4 — Frontend (port 5173)
cd frontend && npm run dev
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Server health check |
| GET | `/api/ollama-status` | Check LLM availability |
| POST | `/api/analyze` | Run full SEO + GEO analysis |
| POST | `/api/report` | Generate PDF report |
| POST | `/api/generate-website` | Generate optimised HTML site |
| POST | `/api/validate` | Run validation loop |
| GET | `/api/projects` | List saved projects |
| GET | `/api/project/<id>` | Get project by ID |

---

## Key Features

**Analysis Pipeline**
- On-page SEO scoring (title, meta, headings, schema markup)
- GEO readiness scoring (citation signals, entity clarity, structured data)
- Semantic similarity comparison against competitors (cosine similarity)
- TF-IDF keyword gap analysis
- Runtime performance tracking (scraping, NLP, generation times)

**PDF Report** *(customer-facing)*
- Overall score with pie chart
- Competitor benchmarking bar chart
- Keyword gap table
- AI-generated recommendations
- Teaser/locked mode for free-tier reports

**Website Generator**
- Feeds all analysis findings into LLM prompt
- Generates schema-rich, SEO/GEO-optimised HTML
- Iterative validation loop with scoring feedback
- Saves generated HTML to MongoDB

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb://127.0.0.1:27017/solrise` |
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM model name | `llama3.2` |
