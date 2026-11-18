# CLI

| Command | Description |
|---------|-------------|
| `runapi init <name> [--docker]` | Scaffold a project |
| `runapi dev` / `runapi start` | Dev server (reload) / production server |
| `runapi routes` | List routes, including `WS` endpoints |
| `runapi generate route\|schema\|repository\|service\|crud <name>` | Generators (`crud` creates a full REST resource) |
| `runapi doctor` | Check environment and project setup |
| `runapi build [-t tag]` | Build a Docker image |
| `runapi db ...` | Alembic migrations |
| `runapi --version` | Show version |
