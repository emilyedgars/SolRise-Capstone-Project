# Atlantic Digital Full-Stack Application

This project consists of a Flask backend for SEO/GEO analysis and a React frontend dashboard.

## Prerequisites

1.  **Python 3.8+**
2.  **Node.js 18+**
3.  **MongoDB** (running locally on port 27017)
4.  **Ollama** (running locally with `qwen2:7b` model)

## Setup Instructions

### 1. Backend Setup

 Navigate to the backend directory:
 ```bash
 cd atlantic-digital/backend
 ```

  Create a virtual environment and install dependencies:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt
  ```

 Download necessary NLP models:
 ```bash
 python -m spacy download en_core_web_sm
 python -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"
 ```

 Start the backend server:
 ```bash
 python app.py
 ```
 The server will start on `http://127.0.0.1:5000`.

### 2. Frontend Setup

 Navigate to the frontend directory:
 ```bash
 cd atlantic-digital/frontend
 ```

 Install dependencies:
 ```bash
 npm install
 ```

 Start the development server:
 ```bash
 npm run dev
 ```
 The application will open in your browser (usually `http://localhost:5173`).

### 3. Services

 Ensure MongoDB is installed and running:
 ```bash
 # If not installed:
 brew tap mongodb/brew
 brew install mongodb-community

 # Start the service:
 brew services start mongodb-community
 ```

 Ensure Ollama is running and the model is pulled:
 ```bash
 ollama serve
 ollama pull qwen2:7b
 ```

## Features

-   **New Analysis**: Run full SEO/GEO analysis on client and competitor URLs.
-   **Dashboard**: View scores, charts, and recommendations.
-   **Website Generator**: Generate optimized HTML using local LLM (Ollama).
-   **GEO Analyzer**: Standalone tool to check "Generative Engine Optimization" readiness.
-   **Projects**: Save and manage analysis reports.

## Troubleshooting

-   **Backend Connection**: If frontend cannot connect to backend, check `vite.config.js` proxy settings and ensure Flask is running on port 5000.
-   **Ollama Errors**: Ensure Ollama is running (`ollama serve`) and accessible at `http://localhost:11434`.
-   **Venv Issues**: Always use `python3 -m pip` instead of `pip` to ensure you're using the venv's pip. Consider installing `direnv` and running `direnv allow` in the `backend/` directory for auto-activation.
