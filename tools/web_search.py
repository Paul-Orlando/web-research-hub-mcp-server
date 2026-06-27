import os
from typing import Optional

import httpx

EXA_API_URL = "https://api.exa.ai/search"


async def web_search(
    query: str,
    num_results: int = 4,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    try:
        api_key = os.environ["EXA_API_KEY"]

        payload: dict = {
            "query": query,
            "numResults": num_results,
            "contents": {
                "summary": {"query": "Summarize the essential results"},
            },
        }
        if start_date:
            payload["startPublishedDate"] = start_date
        if end_date:
            payload["endPublishedDate"] = end_date

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                EXA_API_URL,
                json=payload,
                headers={
                    "x-api-key": api_key,
                    "Content-Type": "application/json",
                },
            )
            response.raise_for_status()
            data = response.json()

        raw_results = data.get("results", [])
        results = [
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                "summary": r.get("summary") or "",
                "published_date": r.get("publishedDate") or "",
            }
            for r in raw_results
        ]
        return {"results": results, "query": query, "total_results": len(results)}
    except Exception:
        return {"results": [], "query": query, "total_results": 0}
