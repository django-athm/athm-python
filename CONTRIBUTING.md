# Contributing

Thank you for your interest in contributing to the ATH Móvil Python unofficial library!

## Quick Start

### Setup

```bash
# Fork and clone the repo
git clone https://github.com/django-athm/athm-python.git
cd athm-python

# Install uv if needed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies and pre-commit hooks
uv sync --all-extras --dev
pre-commit install
```

### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
   - Write clear, readable code
   - Add tests for new functionality
   - Add Google-style docstrings and type hints
   - Update docs if needed

3. **Run tests**
   ```bash
   uv run pytest
   ```

4. **Commit using Conventional Commits**
   ```bash
   git commit -m "feat(client): add new feature"
   git commit -m "fix(models): fix validation bug"
   git commit -m "docs: update readme"
   ```

   Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

5. **Push and open a PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

Pre-commit hooks automatically handle formatting and linting with ruff and mypy. Just commit and they'll run:

- **Formatting**: Ruff auto-formats code (PEP 8, 100 char lines)
- **Linting**: Ruff catches common issues
- **Type checking**: mypy validates type hints
- **Commit messages**: commitizen validates format

To manually run all checks:
```bash
pre-commit run --all-files
```

## Testing

- Place unit tests in `tests/unit/`
- Use descriptive names: `test_create_payment_with_valid_data`
- Mock external API calls with `pytest-httpx`
- Run tests: `uv run pytest`
- Run with coverage: `uv run pytest --cov=athm`

## Documentation

Documentation is in `docs/` using MkDocs:

```bash
# Preview locally
uv run mkdocs serve

# Build
uv run mkdocs build
```

Update relevant docs when adding features.

## Pull Requests

1. Fill out the PR template completely
2. Ensure CI checks pass (tests, linting, type checking)
3. Address review feedback
4. Keep PRs focused on a single feature/fix

Check existing issues before starting work on major changes.

## Reporting Issues

Use the issue templates:
- **Bug Report**: For bugs and unexpected behavior
- **Feature Request**: For new features or enhancements

Include as much detail as possible.

## Questions?

- Check the [documentation](https://athm-python.readthedocs.io)
- Search existing [issues](https://github.com/django-athm/athm-python/issues)
- Open a new issue if needed

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
