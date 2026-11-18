## runapi v0.3.1

Developer-experience polish.

### ✨ Improvements
- **Clearer route errors**: a route file that defines no handlers now logs a warning explaining why the URL returns 404, and suggests renames for near-misses such as `GET` or `get_users` (`app.route_warnings`)
- **`LOG_REQUESTS`**: turn request/response logging on or off independently of `DEBUG` (default: same as `DEBUG`)
- **`DATABASE_URL` checks**: malformed URLs are an error (fatal in production); `postgres://` and URLs without an async driver produce a warning with the exact fix
- **New example**: `examples/basic-crud`, a todo API showing routes -> service -> repository, with curl commands and tests
- Docs: `DATABASE_URL` reference and a routing troubleshooting section
