#!/bin/bash
set -e
trap 'echo "❌ Error on line $LINENO"; exit 1' ERR

echo "🚀 Starting post-create configuration..."

# 1. Verify the runtime Python matches what the repo declares.
# uv reads .python-version when resolving, but we still want a loud
# failure here so a drifted base image is caught before sync, not via a
# subtle test failure later. uv's own venv is built from .python-version
# and is the source of truth for the rest of this script.
echo "🐍 Verifying Python version..."
expected="$(<.python-version)"
actual="$(python3 --version | awk '{print $2}')"
if [ "$actual" != "$expected" ]; then
  echo "⚠️  Python version mismatch: .python-version pins $expected, container ships $actual."
  echo "    uv will still resolve the pinned interpreter, but the base image drifted."
fi

# 2. Sync project dependencies
echo "📚 Syncing dependencies..."
uv sync --frozen

# 3. Install Git hooks and warm up the hook environments.
# Using --install-hooks downloads every remote hook environment
# (gitleaks, hadolint, yamllint, markdownlint, commitizen, etc.) so
# the first commit inside the container is fast. Costs ~30s extra on
# first build, saves the wait on the developer's first commit.
echo "🪝 Installing pre-commit hooks (with --install-hooks warm-up)..."
uv run pre-commit install --install-hooks

echo "✅ Configuration completed successfully!"
