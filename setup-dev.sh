#!/bin/bash

# Development setup script for resume-agent-template-engine

set -e  # Exit on any error

echo "🚀 Setting up development environment..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "❌ uv is required but not installed."
    echo "Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv found"

# Sync dependencies with uv
echo "📦 Syncing dependencies with uv..."
uv sync

# Install pre-commit hooks
echo "🔗 Installing pre-commit hooks..."
uv run pre-commit install

# Format code
echo "✨ Formatting code..."
uv run black src/ tests/

# Run tests to ensure everything works
echo "🧪 Running tests..."
cd src
uv run pytest ../tests/ --maxfail=5
cd ..

echo "🎉 Development environment setup complete!"
echo ""
echo "To run the application:"
echo "uv run python run.py"
echo ""
echo "To run tests:"
echo "cd src && uv run pytest ../tests/"
echo ""
echo "To add dependencies:"
echo "uv add <package-name>"
echo ""
echo "To add dev dependencies:"
echo "uv add --dev <package-name>" 