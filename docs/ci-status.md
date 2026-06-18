# CI Status

The code, docs, tests, UI, devcontainer, and backup workflow files are committed.

Creating files under `.github/workflows/` failed with:

```text
GitHub API 404: Not Found
```

Only workflow paths failed; normal repository files committed successfully. This usually means the GitHub automation token used by the Worker lacks permission to create or update workflow files.

Backup workflow files are available at:

- `docs/workflows/ci.yml`
- `docs/workflows/realtime-validation.yml`

When workflow-file permission is available, copy them to:

- `.github/workflows/ci.yml`
- `.github/workflows/realtime-validation.yml`
