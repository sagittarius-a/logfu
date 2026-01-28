# Contributing

Thanks for your interest in contributing to `log` — welcome! This document explains how to set up a development environment, run the test and quality checks locally, and prepare a pull request.

## Quick start

1. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install the project with development dependencies:

```bash
pip install -e ".[dev]"
```

3. Run the standard checks via `tox` (CI uses the same):

```bash
tox -e py,lint,format,type
```

Run one environment only:

```bash
tox -e py         # run tests
tox -e lint       # ruff lint
tox -e format     # ruff format check
tox -e type       # mypy
```

## Running the checks without `tox`

If you prefer to run tools directly:

```bash
pip install -e ".[dev]"
pytest -q
ruff check .
ruff format --check .
mypy -p log
```

To auto-format with `ruff`:

```bash
ruff format .
```

## Tests

Unit tests are in the `tests/` directory and are run with `pytest`.

```bash
pytest -q
```

## Type checking

Type checks are configured in `pyproject.toml` under `[tool.mypy]`. Run them with:

```bash
mypy -p log
```

If you need stricter checks for a feature branch, consider enabling additional `mypy` flags locally.

## Linting and formatting

We use `ruff` for linting and formatting. Config lives in `pyproject.toml` under `[tool.ruff]`.

- To check linting: `ruff check .`
- To check formatting: `ruff format --check .`
- To apply formatting: `ruff format .`

## CI

CI runs on GitHub Actions and uses `tox` to run:

- `py` (tests)
- `lint` (ruff check)
- `format` (ruff format --check)
- `type` (mypy)

Make sure the above `tox` environments pass locally before opening a PR.

## Pull request workflow

1. Create a topic branch from `main`.
2. Run `tox -e py,lint,format,type` and fix any issues.
3. Keep changes small and focused; include tests for new features or bug fixes.
4. Push your branch and open a PR describing the change and any implementation notes.
5. Address review comments and re-run `tox` before pushing updates.

## Adding tests

- Add unit tests under `tests/`.
- Keep tests deterministic and fast.
- Use `tmp_path` fixtures for filesystem operations.

## Releasing

Releases are created from `main`. Update `pyproject.toml` version and create a changelog entry, then tag and push a release.

## Questions

If something is unclear, open an issue or ping the maintainers on the PR.

Thanks for contributing!
