<!-- markdownlint-disable MD041 -->

## 📋 Summary

Briefly describe the purpose of this Pull Request.

## 🔄 Type of Change

- [ ] ✨ **New Function** (Added a new ETL function in `functions/`)
- [ ] 🐛 **Bug fix** (Non-breaking change which fixes an issue)
- [ ] ♻️ **Refactor** (Code change that improves structure without changing behavior)
- [ ] 🔧 **CI/CD / Tooling** (Changes to workflows or pre-commit)
- [ ] 📚 **Documentation** (Updates to README, CHANGELOG, etc.)

## 📝 Description

Explain the changes in detail:

- Which function(s) are affected?
- What was the specific logic updated?
- Does it require new environment variables or secrets in GitHub?

## 🧪 Testing & Validation

Describe how you verified these changes.

- [ ] **Pre-commit**: I ran `uv run pre-commit run --all-files` and all checks passed.
- [ ] **Tests**: I ran `uv run pytest` and all tests passed.
- [ ] **Linting**: I ran `uv run ruff check .` and `uv run ruff format .` with no errors.
- [ ] **Logs**: Verified Cloud Logging output for successful execution (if applicable).

## ✅ Checklist

- [ ] **Zero Hardcoding**: Verified that no Table IDs, URLs, or Buckets are hardcoded in `main.py` (all in `config.json`).
- [ ] **Idiomatic Python**: Code follows Python 3.12 standards and uses lazy logging.
- [ ] **Documentation**: Updated function-specific README or root CHANGELOG if necessary.
- [ ] **Selective Deploy**: Verified that the GitHub Action only triggers for the affected folder.

## 🔗 Related Issues

Fixes # (issue) or None.
