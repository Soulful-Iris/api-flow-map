# Security and data handling

**What the tooling does**

- Runs locally (or in your CI) as plain Python 3.9+; PyYAML is the only optional dependency.
- Reads source files and, for `diff`, runs read-only git commands (`ls-files`, `rev-parse`,
  `merge-base`, `archive`, `diff`). It never writes to the working tree, the index or remotes.
- Makes **no network calls**. Nothing leaves the machine unless you share the output files.
- Writes only into the output directory you pass with `-o` (default `apiflow-out/`).

**What ends up in the outputs**

- Endpoint routes, handler names, file paths and line numbers, humanised step titles, short
  code snippets (one line each, redacted for API keys, tokens, JWTs, passwords, private keys and
  URL credentials), and — for `diff` — the git diff of the files the changed endpoints touch.
- Treat `flow-*.html/.md/.json` like source code when sharing (they describe internal APIs).
  Use `--no-snippets` and `--no-code-diff` for a version without source text.

**Claude's role**

- Claude runs the scripts and writes the digest/titles. It sees the outputs it renders; the
  usual data-handling rules of your Claude plan apply to the conversation.

**Reporting**

- Open a private issue or contact the CODEOWNERS listed in `.github/CODEOWNERS`.
