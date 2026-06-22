# PR Auditor — Backend

FastAPI + Celery + LangGraph backend. See [docs/PR_Auditor_System_Design.md](../docs/PR_Auditor_System_Design.md) for the full design.

## Layout

```
backend/
  main.py              FastAPI app entrypoint
  requirements.txt
  src/
    core/              config, settings, security (HMAC, JWT), celery app setup
    services/
      ai/              LangGraph graph: state, planner/specialist/critic nodes
      github/          GitHub App auth, installation tokens, diff fetch, comment/check posting
    schemas/           Pydantic models (Finding, PlannerOutput, API request/response)
    models/            SQLAlchemy ORM models (users, installations, repos, reviews, findings, ...)
    utils/             shared helpers
```

## Setup

```
pip install -r requirements.txt
uvicorn main:app --reload
```
