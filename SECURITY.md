# Security Policy

## Supported versions

Security fixes target the latest published version. Currently this is v0.6.1. Older versions do not receive separate backports; update to the latest version.

## Reporting a vulnerability

Do not publish exploit details, API keys, saved credential files, or personal information in an issue.

If GitHub offers **Report a vulnerability** on this repository's Security tab, use that private channel. Otherwise use a private contact method listed on [the Purple Dragon Foundation Ltd website](https://www.purpledragonfoundationltd.xyz/). If neither is available, open an issue titled **Request for private security reporting channel**, without vulnerability details.

Include the affected version and platform, impact, reproduction steps, and a minimal demonstration that does not expose real credentials or private media. Allow the maintainer time to investigate before disclosing details publicly. Response and fix dates depend on availability and severity; no guaranteed timeline is promised.

## Credential and media handling

Saved GIPHY keys use Windows DPAPI tied to the user's Windows account. They are not included in project downloads. Never commit keys or encrypted credential files. If a key is exposed, revoke or rotate it with GIPHY; deleting a repository copy alone does not revoke access.

The app downloads third-party GIFs and processes user-selected media. Keep dependencies current, review source licensing, and avoid sharing private media in reports.
