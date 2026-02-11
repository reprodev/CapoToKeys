# Contributing

## Setup

1. Create a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run tests:

```bash
python -m unittest discover -s tests -v
```

## Development Flow

1. Create a feature branch from `dev`.
2. Keep changes focused and include tests for behavior changes.
3. Ensure CI passes before opening a pull request.

## Coding Guidelines

- Preserve Flask WebUI compatibility as the primary target.
- Keep desktop mode optional and non-blocking for Docker workflows.
- Avoid breaking output naming and archive grouping without migration notes.

## Pull Request Checklist

- [ ] Tests added or updated.
- [ ] `python -m unittest discover -s tests -v` passes.
- [ ] README/docs updated when behavior/config changes.
- [ ] No secrets, local outputs, or build artifacts committed.
