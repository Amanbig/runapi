## runapi v0.1.4

### Release process
- **CI/CD**: Releases are now tag-based. Pushing a `vX.Y.Z` tag builds, publishes to PyPI and creates the GitHub Release; nothing is published on plain pushes to `main`
- **Versioning**: The package version is derived from the git tag (via `hatch-vcs`); `runapi.__version__` reflects it
- **Docs**: Added `RELEASE_NOTES.md` and a `release-notes/` history, plus release instructions in `CONTRIBUTING.md`

### Security & dependencies
- **Security**: Replaced `python-jose` (and its `ecdsa` dependency, both with unfixed advisories) with `PyJWT`
- **Fix**: Pinned `bcrypt<5` — `passlib` is incompatible with bcrypt 5.x and password hashing failed
- Raised minimum versions: `fastapi>=0.115.6`, `python-multipart>=0.0.18`, `uvicorn>=0.30`, `typer>=0.12`, `rich>=13.7`, `aiofiles>=23.2.1`, `psutil>=6.0`
- CI now runs a `pip-audit` dependency scan; Dependabot enabled for pip and GitHub Actions

### Community
- Added `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS` and GitHub Sponsors `FUNDING.yml`

### Fixes & quality
- Code quality fixes across repository, schema, auth and core modules (#14)

### Tests
- Added unit tests for router discovery, detection and nested routing behavior (#13)

### Docs
- README updates (#19) and new issue/PR templates and `CONTRIBUTING.md`
