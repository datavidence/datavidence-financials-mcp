# Security Policy

## Reporting a vulnerability

Please report security issues **privately** — do **not** open a public GitHub
issue or pull request for a suspected vulnerability.

Email **admin@datavidence.ai** with:

- a description of the issue and its impact,
- steps to reproduce (a proof of concept if you have one),
- the affected version or commit, and any relevant configuration.

If you'd like to encrypt your report, ask in a first email and we'll arrange it.

## Scope

In scope:

- this MCP connector (`datavidence-financials`) — the stdio server and its HTTP
  forwarding client, and
- the Datavidence Financials API it talks to (`api.financials.datavidence.ai`).

Out of scope:

- findings that require a compromised local machine or a self-supplied malicious
  API key/base URL,
- volumetric denial-of-service (please don't run load/stress tests against the
  live API), and
- reports from automated scanners with no demonstrated impact.

## Our commitment

- We aim to **acknowledge your report within 5 business days**.
- We'll keep you updated on remediation and let you know when a fix ships.
- **Safe harbor:** we won't pursue or support legal action against good-faith
  research that respects this policy, avoids privacy violations and service
  disruption, and gives us reasonable time to remediate before any disclosure.
- There is **no paid bug-bounty** at this time; we're grateful for responsible
  disclosure and will credit reporters who want it.

## Supported versions

Only the **latest published version** of `datavidence-financials` is supported.
Please reproduce against the current release before reporting.
