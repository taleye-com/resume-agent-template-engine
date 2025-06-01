#!/bin/bash

# Development setup script for resume-agent-template-engine

set -e  # Exit on any error

echo "🚀 Setting up development environment..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
pip install pre-commit
pre-commit install

# Format code
echo "✨ Formatting code..."
black src/ tests/

# Run tests to ensure everything works
echo "🧪 Running tests..."
cd src
PYTHONPATH=$PYTHONPATH:$(pwd) pytest ../tests/ --maxfail=5
cd ..

echo "🎉 Development environment setup complete!"
echo ""
echo "To activate the environment, run:"
echo "source .venv/bin/activate"
echo ""
echo "To run the application:"
echo "python run.py"
echo ""
echo "To run tests:"
echo "cd src && PYTHONPATH=\$PYTHONPATH:\$(pwd) pytest ../tests/" 