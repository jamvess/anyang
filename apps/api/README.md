# anyang-api

FastAPI backend for อ่านยัง?. Conventions: see `CLAUDE.md`. Commands: see the root `CLAUDE.md`.

Docker images build from the repo root so `config/` is included:

```bash
docker build -f apps/api/Dockerfile -t anyang-api .
docker run -p 8080:8080 anyang-api
```
