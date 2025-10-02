#!/bin/bash
# ShambaAI ML Service Setup Script

set -e  # Exit on error

echo "=========================================="
echo "ShambaAI ML Service Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo ""
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo "Installing dependencies (this may take 5-10 minutes)..."
pip install -r requirements.txt

echo ""
echo "✓ Dependencies installed"

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠ Warning: .env file not found"
    echo "Please create .env file with required configuration:"
    echo ""
    echo "  ML_API_KEY=supersecretapexkey"
    echo "  ANTHROPIC_API_KEY=your_claude_api_key"
    echo "  GOOGLE_APPLICATION_CREDENTIALS=/path/to/google-key.json"
    echo "  ML_PORT=8000"
    echo "  DATA_DIR=./data"
    echo ""
    echo "You can copy .env.example to .env and edit it:"
    echo "  cp .env.example .env"
    echo ""
else
    echo ""
    echo "✓ .env file found"
fi

# Check if corpus exists
corpus_count=$(ls -1 data/corpus/*.md 2>/dev/null | wc -l)
if [ "$corpus_count" -eq 0 ]; then
    echo ""
    echo "⚠ No markdown files found in data/corpus/"
    echo "Please run the PDF conversion script:"
    echo ""
    echo "  cd tools"
    echo "  python convert_pdfs.py --input ../../farming_docs --output ../data/corpus"
    echo ""
else
    echo ""
    echo "✓ Found $corpus_count markdown files in corpus"
fi

# Check if index exists
if [ ! -f "data/faiss.index" ]; then
    echo ""
    echo "⚠ FAISS index not found"
    echo "Please build the index:"
    echo ""
    echo "  cd tools"
    echo "  python build_index.py --corpus ../data/corpus --output ../data"
    echo ""
else
    echo ""
    echo "✓ FAISS index found"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Configure .env file (if not done)"
echo "2. Convert PDFs to Markdown (if not done)"
echo "3. Build FAISS index (if not done)"
echo "4. Start the server:"
echo "   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "See README.md for detailed instructions"
echo ""