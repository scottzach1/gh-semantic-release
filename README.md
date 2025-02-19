# gh-semantic-release

Trigger a semantic release with the click of a button

**THIS PROJECT IS CURRENTLY UNDER DEVELOPMENT**

## Concept

- A tool to trigger a GitHub release
    - CLI tool
    - GitHub action published
    - GitHub workflow template provided
- Parse semantic commits to generate structured changelog
- A GitHub workflow template will be provided
- Automatic version bump

### Workflows

1. Trigger a workflow dispatch with a release name to automatically generate a new GitHub release.

    - The version will be bumped based on a configurable heuristic (breaking => major, feat => minor, etc.)
    - The changelog/release summary will be constructed from the parsed commits

2. Configurable via `pyproject.toml`

   ```toml
   [tool.gh-semantic-release]
   types = ["build", "chore", "ci", "docs", "feat"]  # ...
   ```

3. Installed via `pypi`

   Write your own bespoke release behavior using either the CLI or by extending `scottzach1.semantic_release` with your
   own custom python code.
