# Security Policy

## Supported Versions

This repository is in active build-out. Security updates are provided for the `main` branch.

| Version | Supported |
| --- | --- |
| Main (Latest) | :white_check_mark: |
| Archived/Legacy snapshots | :x: |

## Reporting a Vulnerability

We take the security of this infrastructure seriously. If you discover a vulnerability, please follow these steps:

1. **Do NOT create a public GitHub issue.** This allows us to assess the risk before it becomes public knowledge.
2. Email the repository owner directly.
3. Include relevant details:
    * The specific component affected.
    * Description of the vulnerability.
    * Steps to reproduce.

### Response Timeline

* We will acknowledge your report within 48 hours.
* We will provide an estimated timeline for the fix.
* Once fixed, we will notify you and publish a patch via the repository release process.

## Critical Security Rules for Contributors

* **No Hardcoded Secrets:** Never commit API keys, service account JSONs, or passwords.
* **Dependency Management:** Keep dependencies audited (`pip-audit` runs in CI and pre-commit).
