import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.server import TransportSecuritySettings

from tools.calculate import calculate as _calculate
from tools.export_report import export_report as _export_report
from tools.fetch_url import fetch_url as _fetch_url
from tools.web_search import web_search as _web_search

mcp = FastMCP(
    "web-research-hub",
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)


@mcp.tool(
    description=(
        "Searches the live web using Exa AI and returns up to num_results results "
        "with title, URL, summary, and publication date. Use when the query requires "
        "current web sources. Returns empty results array on failure, never throws."
    )
)
async def web_search(
    query: str,
    num_results: int = 4,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    return await _web_search(query, num_results, start_date, end_date)


@mcp.tool(
    description=(
        "Fetches a URL and returns clean extracted text using httpx and BeautifulSoup. "
        "Use when you need the readable content of a specific web page. "
        "Returns success: false on failure, never throws."
    )
)
async def fetch_url(url: str, max_length: int = 5000) -> dict:
    return await _fetch_url(url, max_length)


@mcp.tool(
    description=(
        "Evaluates a safe arithmetic expression using Python's ast module. "
        "Supports +, -, *, /, **, %, //. Use for numeric calculations. "
        "Returns result: null and an error field on failure, never throws."
    )
)
def calculate(expression: str, description: Optional[str] = None) -> dict:
    return _calculate(expression, description)


@mcp.tool(
    description=(
        "Exports a markdown string to PDF, DOCX, or MD format and returns it as "
        "base64-encoded content_base64. Markdown citation links are rendered as "
        "text (domain.com). Returns success: false on failure, never throws."
    )
)
def export_report(content: str, format: str, title: Optional[str] = None) -> dict:
    return _export_report(content, format, title)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="web-research-hub MCP Server", lifespan=lifespan)

_CORS_REGEX = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=_CORS_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "tools": ["web_search", "fetch_url", "calculate", "export_report"]}


app.mount("/", mcp.streamable_http_app())
