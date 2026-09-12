# Publishing api-flow-map

The repository is the single source of truth. Three channels, one codebase.

## 0. One-time setup

1. Create the repository on your GitHub (or GitHub Enterprise) — private/internal is fine.
2. Edit `.claude-plugin/marketplace.json`: `name` (kebab-case; not one of Anthropic's reserved
   names, no "anthropic"/"official" in it), `owner`, `author`. The plugin `name`
   (`api-flow-map`) is the immutable install slug; change `displayName` if you want a nicer label.
3. Replace the handles in `.github/CODEOWNERS`; keep or replace `LICENSE`.
4. Push `main`. CI (`.github/workflows/ci.yml`) validates manifests, skill frontmatter and runs
   the tests on Python 3.9 and 3.12.

## 1. Release

```
# bump the version in BOTH plugins/api-flow-map/.claude-plugin/plugin.json and the marketplace entry
python3 tools/validate.py
git commit -am "api-flow-map 1.0.0" && git tag v1.0.0 && git push --tags
```

The `release` workflow rebuilds `dist/api-flow-map-<version>.skill` / `.zip` and attaches them
to a GitHub Release. Users of the Claude Code marketplace get the update automatically on their
next `/plugin marketplace update` (or auto-update), because `version` changed.

## 2. Channel A — Claude Code (developers)

Users:

```
/plugin marketplace add <owner>/<repo>          # GitHub shorthand; or a full git URL for GHE/GitLab
/plugin install api-flow-map@<marketplace-name>
```

Make it a team default by committing to each service repository's `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": { "<marketplace-name>": { "source": { "source": "github", "repo": "<owner>/<repo>" } } },
  "enabledPlugins": { "api-flow-map@<marketplace-name>": true }
}
```

Organisation-wide (Team/Enterprise): **Organization settings > Plugins** on claude.ai can sync a
private/internal marketplace repository through the Claude GitHub App / GitHub Enterprise App and
provision the plugin to groups. Requirements this repo already meets: relative plugin source
(`./plugins/api-flow-map`), no top-level `bin/` directory, kebab-case names. Admins who lock down
sources use `strictKnownMarketplaces` in managed settings to allowlist this repository.

Private repos: developers need normal git access (`gh auth setup-git` for HTTPS, or SSH keys);
CI runners need a token with read access to the marketplace repo.

## 3. Channel B — claude.ai, Claude Desktop, Cowork (everyone else)

Upload the archive from the release (`api-flow-map-<version>.zip`, contains `SKILL.md`):

- Personal: **Customize > Skills > upload**. Code execution must be enabled.
- Org-wide (Team/Enterprise owners): **Organization settings > Skills > + Add** — provisioned
  to all members, enabled by default. Enterprise orgs can turn on skill content scanning.

## 4. Channel C — Claude API / Agent SDK (automation)

Upload the same archive through the Skills API (`/v1/skills`) and reference the returned
`skill_id` in requests that use the code-execution tool. Note the API sandbox has no network and
no git remote access: run `diff` in your own CI and pass the JSON to Claude if you want a review
written for you.

## 5. Optional — Anthropic's public directory

`anthropics/claude-plugins-official` accepts third-party submissions through its plugin
directory submission form; it reviews for quality and security. Submit the marketplace repo
URL; the layout here matches what the directory expects.

## 6. Pre-push gate (optional, no model involved)

`tools/pre-push` refuses a push when the branch changes the API at `high` risk
or above, so a removed endpoint, a changed auth rule or a changed success
status cannot leave a laptop unnoticed.

```
tools/install-hook.sh                  # into the repo you are standing in
tools/install-hook.sh ~/work/orders-service
```

It runs `apiflow diff --fail-on-risk` and nothing else. **There is no Claude
call in it**, and that is deliberate: the scanner and differ never call a model
(see "Design decisions"), so the gate is deterministic, takes about a second,
and gives the same answer twice. A gate that took minutes and disagreed with
itself would be one people learn to skip, and a skipped gate everyone believes
is running is worse than no gate.

Output goes to `.git/apiflow-out/`, never into the working tree.

| knob | effect |
|---|---|
| `APIFLOW_FAIL_ON=medium git push` | stricter threshold |
| `APIFLOW_SKIP=1 git push` | skip once, visibly |
| `git push --no-verify` | git's own escape hatch |

It fails **open**: if the tool is missing, or git cannot work out a base, or
the analyser errors, the push proceeds with a message on stderr. Blocking a
team's pushes because an optional reviewer is absent is not a trade worth
making.

## Governance checklist

- [ ] CODEOWNERS covers `.claude-plugin/`, `plugins/`, `tools/`
- [ ] Branch protection on `main`; releases only from tags
- [ ] `version` bumped in `plugin.json` (and the marketplace entry) for every release
- [ ] SECURITY.md reviewed by your security partner (no network, read-only git, redaction)
- [ ] Decide who may run `diff` on which repositories (outputs contain source snippets)
