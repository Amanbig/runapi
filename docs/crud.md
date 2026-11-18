# Scaffolding a CRUD resource

```bash
runapi generate crud widget
```

creates a complete in-memory REST resource:

| File | Purpose |
|------|---------|
| `schemas/widget.py` | `WidgetCreate`, `WidgetUpdate`, `WidgetResponse`, ... |
| `repositories/widget.py` | data access (in-memory by default) |
| `services/widget.py` | business logic + `get_widget_service()` shared instance |
| `routes/widget/index.py` | `GET /widget`, `POST /widget` |
| `routes/widget/[id].py` | `GET`, `PUT`, `DELETE /widget/{id}` |

Request bodies are validated with the generated schemas (invalid input returns `422`), missing items return `404`, and `POST` returns `201`.

The generator refuses to overwrite existing files. Data lives in memory; swap the repository for a database-backed one (see [Database](database.md)) before going to production.

Individual pieces are available too: `runapi generate schema|repository|service|route <name>`.
