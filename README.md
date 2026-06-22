# PR Auditor

A multi-agent system that automatically reviews GitHub pull requests for security issues, style problems, missing test coverage, and performance anti-patterns.

A planner agent decides which specialist agents are relevant to a given PR, runs them in parallel, and a critic agent reconciles their findings into a single deduplicated review posted back to GitHub.

## Architecture

```
GitHub PR event → FastAPI webhook → Celery task → LangGraph agent graph
(Planner → Security/Style/TestCoverage/Perf specialists → Critic) → GitHub comment + dashboard
```

See [docs/PR_Auditor_System_Design.md](docs/PR_Auditor_System_Design.md) for the full design.

## Structure

- `backend/` — FastAPI + Celery + LangGraph (ingestion, orchestration, AI reasoning)
- `frontend/` — read-only dashboard
- `docs/` — design documentation
