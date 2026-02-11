# Contributing Guide

Welcome! This document outlines the process for contributing to this project.

## ⚡ Quick Start

### Option 1: Dev Container (Recommended)

Use the provided **Dev Container** (VS Code / GitHub Codespaces). It comes pre-configured with:

- Python 3.12
- uv (package manager)
- just (command runner)
- Google Cloud SDK
- Pre-commit hooks

Open the project in VS Code and select "Reopen in Container".

### Option 2: Manual Setup

**Prerequisites:**

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (package manager)
- [just](https://github.com/casey/just#installation) (command runner)
- Google Cloud SDK (optional, for deployment)

**Setup:**

```bash
# 1. Install dependencies
just sync

# 2. Install pre-commit hooks
just pre-commit-install

# 3. Verify setup
just test
```

---

## 👩‍💻 Development Workflow

1. **Branching:** Create a descriptive branch: `git checkout -b feat/my-feature`.
2. **Development:** Make your changes and run `just test` to verify.
3. **Quality:** Run `just lint` and `just type` before committing (or let pre-commit hooks run automatically).
4. **Commits:** Use conventional commits (e.g., `feat:`, `fix:`, `docs:`).

---

## 🚀 Creating a New Function

1. **Structure:** Create a new folder under `functions/ingestion/` or `functions/trigger/`.
2. **Files:**
    - `main.py`: The function logic with `main()` entry point.
    - `requirements.txt`: Python dependencies.
    - `config.template.json`: A sanitized version of your configuration.
    - `README.md`: Local documentation (business logic and mappings).
    - `deploy.json`: (Optional) Custom deployment settings.
3. **CI/CD:** Push your changes - the workflow automatically detects and deploys new functions.

---

## 📦 Secrets Management

This project uses **GitHub Environment Secrets and Variables** for production configurations.

All deployment credentials are configured in the `prd` environment.

For details on required secrets and variables, see **[CI/CD Documentation](docs/cicd.md#required-github-configuration)**.
