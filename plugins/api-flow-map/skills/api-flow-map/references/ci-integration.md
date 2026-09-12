# CI integration

`apiflow.py diff` is deterministic, needs only Python 3.9+ and git history, and exits with
`4` when `--fail-on-risk <level>` is reached. Attach `flow-diff.html` as an artifact and post
`flow-diff.md` as the PR comment.

## GitHub Actions

```yaml
name: api-flow-review
on: [pull_request]
jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }                  # diff needs the base branch history
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install pyyaml                   # optional: YAML specs / serverless.yml
      - name: Diff API flows against the PR base
        run: |
          python3 tools/api-flow-map/scripts/apiflow.py diff . \
            --base origin/${{ github.base_ref }} -o apiflow-out --fail-on-risk high
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: api-flow-review, path: apiflow-out }
      - name: Comment on the PR
        if: always()
        uses: marocchino/sticky-pull-request-comment@v2
        with: { path: apiflow-out/flow-diff.md }
```

Make the gate advisory by dropping `--fail-on-risk`, or use `medium` for services with strict
contracts. A `.apiflow.json` in the repo (e.g. `base_branch`, `include`) is picked up automatically.

## Jenkins (declarative)

```groovy
stage('API flow review') {
  steps {
    sh 'git fetch origin ${CHANGE_TARGET}:refs/remotes/origin/${CHANGE_TARGET}'
    sh 'python3 tools/api-flow-map/scripts/apiflow.py diff . --base origin/${CHANGE_TARGET} -o apiflow-out || test $? -eq 4'
    archiveArtifacts artifacts: 'apiflow-out/*', fingerprint: true
  }
}
```

## Exit codes

| code | meaning |
|---|---|
| 0 | completed |
| 1 | usage or unexpected error |
| 2 | completed with diagnostics (`--strict`) or no endpoints found |
| 3 | git problem (not a repo, base ref missing) |
| 4 | `--fail-on-risk` threshold reached |

## Tips

- Keep the skill scripts in the repo (`tools/api-flow-map/`) or a shared tooling repo so CI
  runs the same version reviewers use locally.
- `--with-models` also writes the base and head `flow-model-*.json`, useful for tracking API
  surface over time.
- Large monorepos: `--include "services/orders/**"` or `include` in `.apiflow.json`.
