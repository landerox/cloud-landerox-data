# just -- A handy command runner.
# See https://github.com/casey/just
# To run: `just <command>`

# Default recipe when no command is specified
default:
  @just --list

# ==============================================================================
# Setup & Maintenance
# ==============================================================================

# Installs locked Python dependencies with uv (uses uv.lock).
sync:
  @echo "📦 Syncing Python dependencies with uv..."
  uv sync --frozen
  @echo "✅ Dependencies synced."

# Upgrades dependencies to the latest versions allowed by pyproject.toml.
deps-update:
  @echo "⬆️  Upgrading dependencies (pyproject.toml ranges)..."
  uv sync --upgrade
  @echo "✅ Done. Review uv.lock before committing."

# Shows the resolved dependency tree.
deps-tree:
  @uv tree

# Cleans up the virtual environment and cache files.
clean:
  @echo "🧹 Cleaning virtual environment and caches..."
  rm -rf ./.venv ./.ruff_cache ./.pytest_cache ./__pycache__
  @echo "✅ Cleaned."

# ==============================================================================
# Quality Assurance
# ==============================================================================

# Runs every pre-commit hook against all files (mirrors CI scope).
lint:
  @echo "🔍 Running all pre-commit hooks on all files..."
  uv run pre-commit run --all-files

# Applies ruff auto-fixes and formatting.
format:
  @echo "🔧 Applying ruff fixes and formatting..."
  uv run ruff check --fix .
  uv run ruff format .

# Runs static type analysis with pyright (strict mode).
type:
  @echo "📝 Running static type analysis with pyright..."
  uv run pyright

# Runs pytest for unit and integration tests.
test:
  @echo "🧪 Running tests with pytest..."
  uv run pytest

# Runs tests with coverage (same gate as CI: --cov-fail-under=90 on shared/**).
coverage:
  @echo "📊 Running tests with coverage..."
  uv run pytest --cov --cov-report=term-missing --cov-report=xml

# Audits dependencies for known vulnerabilities.
audit:
  @echo "🛡️  Auditing dependencies with pip-audit..."
  uv run pip-audit

# Builds the shared/common wheel + sdist into dist/.
build:
  @echo "📦 Building wheel and sdist with uv build..."
  rm -rf dist
  uv build
  @echo "✅ Artifacts in ./dist/"

# Runs the full quality gate (lint + type + test + audit), same as CI.
check: lint type test audit
  @echo "✅ All quality checks passed."

# ==============================================================================
# Pre-commit Hooks
# ==============================================================================

# Installs pre-commit hooks in the git repository.
pre-commit-install:
  @echo "➕ Installing pre-commit hooks..."
  uv run pre-commit install
  @echo "✅ Pre-commit hooks installed."

# Updates pre-commit hooks to their latest versions.
pre-commit-update:
  @echo "⬆️  Updating pre-commit hooks..."
  uv run pre-commit autoupdate
  @echo "✅ Pre-commit hooks updated."

# ==============================================================================
# Local Development & Emulators
# ==============================================================================

# Starts the Pub/Sub emulator.
emulator-pubsub:
  @echo "🚀 Starting Pub/Sub emulator on :8085..."
  gcloud beta emulators pubsub start --project=local-project --host-port=0.0.0.0:8085

# Hint for the BigQuery emulator (requires Docker + goccy/bigquery-emulator).
emulator-bigquery:
  @echo "💡 BigQuery emulator is not bundled with this devcontainer."
  @echo "   Run on the host (or a docker-enabled environment):"
  @echo "   docker run --rm -p 9050:9050 ghcr.io/goccy/bigquery-emulator:latest \\"
  @echo "     --project=local-project"
