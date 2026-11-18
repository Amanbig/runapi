# CRUD example: a todo API

A small REST API showing file-based routing, validation, a service layer and a repository.

```bash
pip install runapi
cp .env.example .env      # then set SECRET_KEY
runapi dev
```

| Request | File |
|---------|------|
| `GET /todos`, `POST /todos` | `routes/todos/index.py` |
| `GET /todos/{id}`, `PUT /todos/{id}`, `DELETE /todos/{id}` | `routes/todos/[id].py` |

```bash
curl -X POST localhost:8000/todos -H 'content-type: application/json' -d '{"title": "write docs"}'
curl localhost:8000/todos
curl -X PUT localhost:8000/todos/1 -H 'content-type: application/json' -d '{"done": true}'
curl 'localhost:8000/todos?done=true'
curl -X DELETE localhost:8000/todos/1
```

Interactive docs: http://localhost:8000/docs

## How it fits together

```
route (HTTP)  ->  service (rules)  ->  repository (storage)
```

Data is stored in memory and resets on restart. To keep data, replace
`InMemoryRepository` with a database repository: see the
[database docs](https://github.com/Amanbig/runapi/blob/main/docs/database.md).

Want the same thing generated for your own resource? Run `runapi generate crud <name>`.
