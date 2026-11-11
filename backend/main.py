import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

import lakes

app = FastAPI(title="Fisher API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/lakes/search")
async def lakes_search(q: str = Query(..., min_length=2)):
    try:
        found = await lakes.search_lakes(q)
    except httpx.HTTPError as e:
        raise HTTPException(502, f"Lake lookup failed: {e}")
    return {"query": q, "results": found}
