import httpx
from bs4 import BeautifulSoup


async def fetch_url(url: str, max_length: int = 5000) -> dict:
    try:
        async with httpx.AsyncClient(
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (compatible; web-research-hub/1.0)"},
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, "html.parser")

        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        content = soup.get_text(separator="\n", strip=True)
        content = content[:max_length]

        return {"url": url, "content": content, "title": title, "success": True}
    except Exception as exc:
        return {"url": url, "content": "", "title": "", "success": False, "error": str(exc)}
