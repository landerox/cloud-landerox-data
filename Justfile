# just -- A handy command runner.
# See https://github.com/casey/just
# To run: `just <command>`

# Default recipe when no command is specified
default:
  @just --list

# ==============================================================================
# Setup & Maintenance
# ==============================================================================

# Installs/updates Python dependencies using uv.
# Runs `uv sync` to ensure the virtual environment matches uv.lock.
sync:
  @echo "📦 Syncing Python dependencies with uv..."
  uv sync --frozen
  @echo "✅ Dependencies synced."

# Cleans up the virtual environment and cache files.
clean:
  @echo "🧹 Cleaning virtual environment and cache..."
  rm -rf ./.venv ./.ruff_cache ./__pycache__
  @echo "✅ Cleaned."

# ==============================================================================
# Quality Assurance
# ==============================================================================

# Runs all quality, security, and formatting checks via pre-commit.
lint:
  @echo "🔍 Running all pre-commit hooks on all files..."
  uv run pre-commit run --all-files

# Applies ruff auto-fixes and formatting.
format:
  @echo "🔧 Applying ruff fixes and formatting..."
  uv run ruff check --fix .
  uv run ruff format .

# Runs static type analysis with ty.
type:
  @echo "📝 Running static type analysis with ty..."
  uv run ty check

# Runs pytest for unit and integration tests.
test:
  @echo "🧪 Running tests with pytest..."
  uv run pytest

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
  @echo "⬆️ Updating pre-commit hooks..."
  uv run pre-commit autoupdate
  @echo "✅ Pre-commit hooks updated."

# ==============================================================================
# Local Development & Emulators
# ==============================================================================

# Starts the Pub/Sub emulator.
emulator-pubsub:
  @echo "🚀 Starting Pub/Sub emulator..."
  gcloud beta emulators pubsub start --project=local-project

# Starts the BigQuery emulator.
# Requires: npm install -g @minio/bigquery-emulator or similar
emulator-bigquery:
  @echo "🚀 Starting BigQuery emulator (requires separate setup)..."
  @echo "💡 Hint: consider using https://github.com/goccy/bigquery-emulator"
