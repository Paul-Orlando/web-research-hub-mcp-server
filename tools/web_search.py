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
        api_key = os.environ.get("EXA_API_KEY")
        if not api_key:
            print("[web_search] EXA_API_KEY is not set; returning empty results", flush=True)
            return {"results": [], "query": query, "total_results": 0}

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
    except httpx.HTTPStatusError as e:
        try:
            body = e.response.text[:300]
        except Exception:
            body = "<unreadable>"
        print(
            f"[web_search] Exa HTTP {e.response.status_code}: {body!r}",
            flush=True,
        )
        return {"results": [], "query": query, "total_results": 0}
    except Exception as e:
        print(f"[web_search] {type(e).__name__}: {e}", flush=True)
        return {"results": [], "query": query, "total_results": 0}
