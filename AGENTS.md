## Developer Notes (Humans and Agents)

This file is for contributors and automation. End-user instructions belong in `README.md`.

### Project setup

- Dependency manager: `uv`
- Source: `src/`
- Tests: `tests/` (when present)

### Required checks

All code must pass these exact commands before merging:

```
uv run pytest
uv run ruff format src tests
uv run ruff check --fix src tests
uv run mypy src
```

### Coding guidelines

- Keep code ASCII unless a file already uses Unicode.
- Prefer small, focused helpers; avoid hidden side effects.
- Update or add tests when behavior changes.
