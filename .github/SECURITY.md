# Security Policy

## Supported Versions

This repository is in active build-out. Security updates are provided for the `main` branch.

| Version | Supported |
| --- | --- |
| Main (Latest) | :white_check_mark: |
| Archived/Legacy snapshots | :x: |

## Reporting a Vulnerability

We take the security of this infrastructure seriously. If you discover a vulnerability, please follow these steps:

1. **Do NOT create a public GitHub issue.** Public disclosure before a fix is coordinated puts users at risk.
2. Use one of the private channels below (in order of preference):
    * **Preferred:** Open a private report via GitHub Security Advisories:
      [https://github.com/landerox/cloud-landerox-data/security/advisories/new](https://github.com/landerox/cloud-landerox-data/security/advisories/new)
    * **Fallback:** Email the repository owner at `landerox@gmail.com` with the subject line `[SECURITY] cloud-landerox-data`.
3. Include relevant details:
    * The specific component affected (file path, function, or workflow).
    * Description of the vulnerability and its potential impact.
    * Steps to reproduce, ideally with a minimal example.
    * Any suggested remediation, if known.

### Response Timeline

* We will acknowledge your report within 48 hours.
* We will provide an initial assessment and estimated timeline for the fix within 7 days.
* Once fixed, we will notify you, publish a patch via the repository release process, and (with your consent) credit you in the advisory.

## Critical Security Rules for Contributors

* **No Hardcoded Secrets:** Never commit API keys, service account JSONs, or passwords.
* **Dependency Management:** Keep dependencies audited (`pip-audit` runs in CI and pre-commit).
