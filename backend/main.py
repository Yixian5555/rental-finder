import asyncio
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import parser as _parser
from scrapers.craigslist import scrape as cl_scrape
from scrapers.kijiji import scrape as kj_scrape
from scrapers.livrent import scrape as lr_scrape

app = FastAPI()

FRONTEND_DIR = Path(__file__).parent.parent / "frontend"


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class SearchRequest(BaseModel):
    filters: dict


@app.get("/")
def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/chat")
async def chat(req: ChatRequest):
    result = await asyncio.to_thread(_parser.process_chat, [m.model_dump() for m in req.messages])
    return result


@app.post("/search")
async def search(req: SearchRequest):
    filters = req.filters

    results = await asyncio.gather(
        asyncio.to_thread(cl_scrape, filters),
        asyncio.to_thread(kj_scrape, filters),
        asyncio.to_thread(lr_scrape, filters),
        return_exceptions=True,
    )

    listings = []
    for r in results:
        if isinstance(r, list):
            listings.extend(r)

    seen = set()
    unique = []
    for item in listings:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)

    unique.sort(key=lambda x: x.get("price", 999999))
    return {"listings": unique, "count": len(unique)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
