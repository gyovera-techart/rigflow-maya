# Security Policy

## Supported version

The current public baseline is **RigFlow v0.1.0**.

## Reporting a vulnerability

Please do not disclose security vulnerabilities in public issues.

If you discover a security issue involving credentials, arbitrary code execution, unsafe file handling, or another security-sensitive behavior, report it privately to the repository maintainer through the contact method published in the GitHub repository profile.

When reporting an issue, include:

- affected version;
- reproduction steps;
- expected and observed behavior;
- relevant logs or screenshots, after removing private data and credentials.

Do not include API keys, passwords, access tokens, private keys, or other secrets in the report.

## Secret-handling policy

RigFlow v0.1.0 does not require API keys, cloud credentials, passwords, or external service tokens. Local configuration is optional and is intended for non-secret validation settings.

Never commit real credentials, `.env` files, private keys, production scene files, or private client/project assets to this repository.
