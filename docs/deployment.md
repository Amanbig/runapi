# Deployment

```bash
runapi init my-api --docker
cd my-api
runapi build -t my-api
docker run -p 8000:8000 -e SECRET_KEY=... my-api
```

Always set `SECRET_KEY` and `DEBUG=false` in production.
