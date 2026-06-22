from fastapi import FastAPI

app = FastAPI(title="PR Auditor")


@app.get("/health")
async def health():
    return {"status": "ok"}
