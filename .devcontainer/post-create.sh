#!/bin/bash
set -e
trap 'echo "❌ Error on line $LINENO"; exit 1' ERR

echo "🚀 Starting post-create configuration..."

# 1. Sync project dependencies
echo "📚 Syncing dependencies..."
uv sync --frozen

# 2. Install Git hooks
echo "🪝 Installing pre-commit hooks..."
uv run pre-commit install

echo "✅ Configuration completed successfully!"
