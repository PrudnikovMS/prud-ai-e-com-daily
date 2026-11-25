# Security policy

The current development line is 0.2.x. The reporting core operates offline; experimental opt-in API collectors use locally supplied environment variables and fixed marketplace hosts. There is no remote delivery, shared credential storage, or live-account validation. Raw responses and signed report links are sensitive. Store them only in the ignored private/ directory with appropriate OS permissions; gitignore is not encryption. Never upload them or place them in public logs.

Do not post vulnerabilities containing private data, seller credentials, or tokens in public issues. Use GitHub private vulnerability reporting if enabled, or contact the repository maintainer privately via a published contact method. Include a minimal synthetic reproduction, affected version and impact. Do not access other sellers' accounts or test against third-party services without permission.

For future integrations, use least-privilege read-only credentials, redact logs, store secrets outside the repository and require explicit confirmation for delivery or other external side effects. Never commit production exports. If a credential is exposed, revoke or rotate it immediately; removing it from the latest commit alone is insufficient.
