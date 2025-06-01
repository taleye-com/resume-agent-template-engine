#!/bin/bash

# Status check script for resume-agent-template-engine

set -e  # Exit on any error

echo "🔍 Checking project status..."

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Run 'source .venv/bin/activate' first."
    exit 1
fi

echo "✅ Virtual environment activated"

# Check code formatting
echo "🎨 Checking code formatting..."
if black --check src/ tests/ > /dev/null 2>&1; then
    echo "✅ Code formatting is correct"
else
    echo "❌ Code formatting issues found. Run 'black src/ tests/' to fix."
    exit 1
fi

# Run type checking
echo "🔍 Running type checking..."
cd src
if PYTHONPATH=$PYTHONPATH:$(pwd) mypy --namespace-packages --ignore-missing-imports resume_agent_template_engine/ > /dev/null 2>&1; then
    echo "✅ Type checking passed"
else
    echo "⚠️  Type checking issues found (this won't fail CI)"
fi

# Run tests
echo "🧪 Running tests..."
if PYTHONPATH=$PYTHONPATH:$(pwd) pytest ../tests/ --maxfail=1 -q > /dev/null 2>&1; then
    echo "✅ All tests passed"
else
    echo "❌ Some tests failed. Run tests manually to see details."
    cd ..
    exit 1
fi

cd ..

# Check if pre-commit hooks are installed
if [ -f ".git/hooks/pre-commit" ]; then
    echo "✅ Pre-commit hooks are installed"
else
    echo "⚠️  Pre-commit hooks not installed. Run 'pre-commit install' to set them up."
fi

echo ""
echo "🎉 All checks passed! Your local environment is ready for CI." 