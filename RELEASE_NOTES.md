## runapi v0.2.0

A big release: richer routing, WebSockets, token revocation, database migrations, a safer dependency stack, and tag-based releases.

### ⚠️ Breaking changes
- **Python 3.10+ is now required** (3.8 and 3.9 are dropped; 3.13 is supported)
- `python-jose` was replaced by `PyJWT` and `passlib` by `bcrypt`. If you import either library through runapi's internals, update your code. Existing `$2b$` password hashes keep working
- Catch-all routes (`[...slug].py`) now actually behave as catch-alls; previously they were treated as a plain dynamic route

### ✨ New features
- **Routing**: dynamic folders (`routes/users/[id]/posts.py` -> `/users/{id}/posts`), route groups (`routes/(admin)/...`, not part of the URL), and deterministic ordering (static, then dynamic, then catch-all)
- **WebSockets**: define `async def websocket(ws)` in a route file
- **Auth**: token revocation (`revoke_token`, pluggable `TokenBlacklist`) and refresh-token rotation (`rotate_refresh_token`); tokens now carry a `jti`
- **Database**: `runapi db init|migrate|upgrade|downgrade` (Alembic) and the `runapi[db]` extra
- **CLI**:
  - `runapi --version` / `-V`
  - `runapi doctor` checks Python, project layout and `SECRET_KEY`
  - `runapi build` builds a Docker image
  - `runapi init --docker` generates `Dockerfile`, `.dockerignore` and `requirements.txt`
  - `runapi init` now generates a random `SECRET_KEY` in `.env`
  - `runapi routes` uses the router's path rules and shows `WS` endpoints
- **Docs & examples**: `examples/basic` (covered by tests) and a MkDocs site in `docs/` (`runapi[docs]`)

### 🔒 Security & dependencies
- Removed `python-jose` and `ecdsa` (open advisories with no fix) in favour of `PyJWT`
- Fixed `hash_password` crashing with bcrypt 5.x by using `bcrypt` directly
- Raised minimum versions: `fastapi>=0.115.6`, `python-multipart>=0.0.18`, `uvicorn>=0.30`, `typer>=0.12`, `rich>=13.7`, `aiofiles>=23.2.1`, `psutil>=6.0`
- CI runs `pip-audit`; Dependabot is enabled for pip and GitHub Actions; added `SECURITY.md`

### 🚀 Release process
- Releases are **tag-based**: pushing a `vX.Y.Z` tag tests, builds, publishes to PyPI and creates the GitHub Release. Nothing is published from plain pushes to `main`
- The package version comes from the git tag (`hatch-vcs`); `runapi.__version__` reflects it
- Added `RELEASE_NOTES.md` and the `release-notes/` history; see `CONTRIBUTING.md`

### 🧹 Quality & community
- Code quality fixes across repository, schema, auth and core modules (#14)
- New tests for router discovery, nested routing, CLI, token revocation and the example app (#13)
- `py.typed`, a pre-commit config, GitHub Actions bumped to current majors
- Added `CODE_OF_CONDUCT.md`, `CODEOWNERS`, GitHub Sponsors `FUNDING.yml`, issue/PR templates and README updates (#19)

**Full changelog**: https://github.com/Amanbig/runapi/compare/v0.1.3...v0.2.0
