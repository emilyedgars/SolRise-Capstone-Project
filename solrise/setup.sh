#!/bin/bash

# Atlantic Digital Setup Script

echo "🌊 Atlantic Digital Setup"
echo "========================"

# 1. Check Prerequisites
echo "Step 1: Checking environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
else
    echo "✅ Python 3 found"
fi

# Check for Node.js (and attempt to catch the library error)
echo "Checking Node.js..."
if ! node -v &> /dev/null; then
    echo "⚠️  Node.js seems to be having issues or is not installed."
    echo "   (If you saw a 'dyld: Library not loaded' error earlier, try running: brew reinstall node)"
else
    echo "✅ Node.js found"
fi

# 2. Setup Backend
echo ""
echo "Step 2: Setting up Backend..."
cd backend
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Upgrading pip..."
python3 -m pip install --upgrade pip

echo "Installing dependencies (this may take a minute)..."
python3 -m pip install -r requirements.txt
python3 -m playwright install

echo "Downloading NLP models..."
python3 -m spacy download en_core_web_sm
python3 -c "import nltk; nltk.download('stopwords'); nltk.download('wordnet')"

if command -v direnv &> /dev/null; then
    echo "✅ direnv found, allowing .envrc..."
    echo "layout python" > .envrc
    direnv allow
else
    echo "💡 Tip: Install 'direnv' (brew install direnv) to auto-activate this venv when you cd into backend/"
    echo "source .venv/bin/activate" > .envrc
fi

cd ..

# 3. Setup Frontend
echo ""
echo "Step 3: Setting up Frontend..."
cd frontend
if [ -f "package.json" ]; then
    echo "Installing frontend dependencies..."
    npm install
else
    echo "❌ frontend/package.json not found!"
fi
cd ..

# 4. Success Message
echo ""
echo "✅ Setup Complete!"
echo "========================"
echo "To run the application, you need two terminals:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd atlantic-digital/backend"
echo "  source venv/bin/activate"
echo "  python3 app.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd atlantic-digital/frontend"
echo "  npm run dev"
echo ""
echo "Don't forget to ensure MongoDB and Ollama are running!"
