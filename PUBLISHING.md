# Publishing & directory listing — step by step

The four directories you named (Smithery, Glama, mcp.so, PulseMCP) are not four
independent forms. In 2026 they key off **a public GitHub repo + the official MCP
registry**, which Smithery/Glama/PulseMCP ingest automatically. So the order is:
public repo → republish PyPI 0.1.1 → official registry → then the directories.

Everything below is a command you run (repo creation, `git push`, `twine`,
`mcp-publisher` all need your GitHub/PyPI credentials).

---

## Part A — Create the public repo

Create `datavidence/datavidence-financials-mcp` (Public) under the Datavidence org,
then push this folder:

```bash
cd datavidence-financials-mcp
git init
git add .
git commit -m "Datavidence Financials MCP server (public open-source connector)"
git branch -M main
git remote add origin https://github.com/datavidence/datavidence-financials-mcp.git
git push -u origin main
```

(Or `gh repo create datavidence/datavidence-financials-mcp --public --source=. --push`.)

**Verify:** the repo loads publicly and shows the README.

---

## Part B — Republish PyPI `0.1.1` (fixes the broken links + adds the registry ownership line)

The current 0.1.0 on PyPI points its Repository/Documentation links at a **private
404 repo**, and lacks the `mcp-name:` line the registry needs to validate PyPI
ownership. 0.1.1 fixes both (corrected `[project.urls]`, and the
`<!-- mcp-name: io.github.datavidence/datavidence-financials -->` line is already in
the README).

```bash
cd datavidence-financials-mcp
rm -rf dist build *.egg-info
python -m build
twine check dist/*
twine upload dist/*          # uses your ~/.pypirc (__token__ + PyPI token in Keychain)
```

**Verify:** https://pypi.org/project/datavidence-financials/0.1.1/ shows the fixed
links, and `uvx datavidence-financials` still runs the four tools.

---

## Part C — Publish to the official MCP registry (this feeds the directories)

```bash
brew install mcp-publisher          # or the curl one-liner from the registry docs
cd datavidence-financials-mcp       # server.json lives here
mcp-publisher login github          # device flow — authorize as the Datavidence org owner
mcp-publisher publish               # reads ./server.json
```

- Namespace `io.github.datavidence/*` is authorized by logging in as a GitHub owner
  of the `datavidence` org.
- PyPI package ownership is validated by the `mcp-name:` line in the 0.1.1 README.

**Verify:** search `datavidence-financials` at https://registry.modelcontextprotocol.io.

**Alternative namespace (optional):** if you'd rather anchor to the domain, use
`mcp-publisher login dns --domain datavidence.ai --private-key <key>` and rename the
server in `server.json` to `com.datavidence/financials`. Not required — the GitHub-org
namespace is simpler and already set.

---

## Part D — The four directories

- **Smithery, Glama, PulseMCP** — no form. They ingest the registry and crawl the
  public repo on their own cadence (hours to a few days after Part C). Once each
  entry appears, **claim it** to verify ownership and polish the copy:
  - Glama: open your server's page → "Claim" (add a `glama.json` if it asks, then verify).
  - PulseMCP: open your server's page → "Claim this server".
  - Smithery: it should appear from the registry; connect the GitHub repo to verify.
- **mcp.so** — has a submit form: https://mcp.so/submit?type=server. Paste the repo
  URL (`https://github.com/datavidence/datavidence-financials-mcp`). Free review, or
  $39 to skip the queue. Use the copy in `LISTINGS.md`.

Use `LISTINGS.md` for the title, descriptions, category, and keywords wherever a
directory lets you edit them.
