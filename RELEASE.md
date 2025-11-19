# Release Workflow

## Quick Start

### Daily Development
Use conventional commits:
```bash
git commit -m "feat: add new feature"    # New feature
git commit -m "fix: resolve bug"         # Bug fix
git commit -m "docs: update readme"      # Documentation
```

### Making a Release

```bash
# 1. Update version (from main branch)
cz bump --patch    # Bug fixes (0.2.0 → 0.2.1)
cz bump --minor    # New features (0.2.0 → 0.3.0)
cz bump --major    # Breaking changes (0.2.0 → 1.0.0)

# 2. Push to GitHub
git push && git push --tags

# 3. Done! GitHub Actions handles the rest
```

The automation will:
- Update version in code
- Generate CHANGELOG
- Create GitHub Release
- Publish to PyPI (after approval)

### Test Release (Optional)

Test on TestPyPI first:
1. Go to GitHub Actions → "Release" workflow
2. Click "Run workflow" → Enter version
3. Install: `pip install -i https://test.pypi.org/simple/ athm==VERSION`

### If Something Goes Wrong

```bash
# Delete tag and try again
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z
```
