# web-research-hub-mcp-server
### FastAPI · FastMCP · Streamable HTTP · Exa AI · Python

A standalone MCP server that exposes the Web Research Hub's core
research capabilities as standardized tools over Streamable HTTP —
callable by Claude Desktop, Claude.ai, or any MCP-compatible agent
or client.

Built as the infrastructure layer for
[web-research-hub](https://github.com/Paul-Orlando/web-research-hub),
this server separates tool execution from agent reasoning: the LLM
stays in the research app, the tools live here.

---

## 🔗 Live Endpoint

```
https://web-production-a8829.up.railway.app/mcp
```

Health check:
```
https://web-production-a8829.up.railway.app/health
```

---

## Architecture

```
Client (Claude Desktop / Claude.ai / custom agent)
        │  POST /mcp  (MCP Streamable HTTP)
        ▼
  FastAPI + FastMCP
        │
  ┌─────┴────────────────────────────────────────┐
  │  web_search  fetch_url  calculate  export_report  │
  └─────┬──────────────────────────────────────────┘
        │
   Exa AI API    httpx + BS4    ast (stdlib)    fpdf2 / python-docx
```

- **Transport:** Streamable HTTP — clients POST to `/mcp`
- **Health check:** `GET /health` — public, no auth required
- **CORS:** configurable via `CORS_ORIGIN_REGEX` env var

---

## How It Fits the Portfolio

This server is part of a three-tier architecture:

```
Web Research Hub (frontend + FastAPI backend)
  → calls this MCP server as a tool provider
  → agents use web_search and fetch_url during research
  → reports exported via export_report

This MCP Server
  → exposes 4 tools over Streamable HTTP
  → no LLM calls inside — pure tool execution
  → callable by any MCP-compatible client independently

Pinecone Agentic Search MCP Server
  → separate MCP server in this portfolio
  → handles academic/vector search over ArXiv corpus
  → uses SSE transport (contrast: this server uses
    Streamable HTTP — the newer MCP spec standard)
```

The two MCP servers in this portfolio demonstrate both transport
patterns (SSE and Streamable HTTP) and two different tool scopes
(single-purpose vector search vs. broader research toolkit).

---

## What Makes This Different from the Pinecone MCP Server

| | Pinecone MCP Server | This Server |
|---|---|---|
| Transport | SSE | Streamable HTTP |
| Tools | 1 (`agentic-search`) | 4 (`web_search`, `fetch_url`, `calculate`, `export_report`) |
| Data source | Pinecone vector store (ArXiv corpus) | Live web (Exa AI) + stdlib |
| LLM calls | Yes (OpenRouter) | None — pure tool execution |
| Purpose | Academic/research paper search | Web research tool layer |

---

## Tool Reference

### `web_search`

Searches the live web via Exa AI and returns structured results
with title, URL, summary, and publication date. Use when the
research query requires current, real-world web sources. Returns
an empty results array on failure, never throws.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `query` | string | required | Search query |
| `num_results` | int | `4` | Max results to return |
| `start_date` | string | `null` | ISO 8601 date filter (e.g. `2024-01-01`) |
| `end_date` | string | `null` | ISO 8601 date filter |

**Response:**
```json
{
  "results": [{ "title": "", "url": "", "summary": "", "published_date": "" }],
  "query": "...",
  "total_results": 4
}
```
Returns `results: []` on failure, never throws.

---

### `fetch_url`

Fetches a URL and returns clean extracted text, stripping HTML
and truncating to the specified character limit. Use to go deeper
on a specific source found during web search. Returns
`success: false` on failure, never throws.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `url` | string | required | Full URL to fetch |
| `max_length` | int | `5000` | Character limit on returned content |

**Response:**
```json
{ "url": "", "content": "", "title": "", "success": true }
```

---

### `calculate`

Evaluates a safe arithmetic expression using Python's AST parser —
no raw `eval()`. Use for numeric reasoning within research tasks
(e.g. percentage changes, cost calculations, financial figures).
Returns `result: null` with an error field on failure, never throws.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `expression` | string | required | e.g. `"(3 + 4) * 2"` |
| `description` | string | `null` | Optional label for context |

Supported operators: `+  -  *  /  **  %  //`

**Response:**
```json
{ "expression": "(3 + 4) * 2", "result": 14, "description": null }
```

---

### `export_report`

Exports a markdown string to PDF, DOCX, or MD and returns the
file as a base64-encoded string. Citation links `[text](url)` are
rendered as `text (domain.com)` in PDF and DOCX output so sources
remain identifiable outside the browser. Returns `success: false`
on failure, never throws.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `content` | string | required | Markdown source |
| `format` | string | required | `"pdf"`, `"docx"`, or `"md"` |
| `title` | string | `null` | Prepended as H1; used in filename |

**Response:**
```json
{
  "format": "pdf",
  "filename": "report.pdf",
  "content_base64": "...",
  "success": true
}
```

---

## Design Constraints

**No LLM calls inside this server.**
Every tool is a pure function: input → deterministic output.
The LLM reasoning (planning, orchestration, synthesis) stays in
the Web Research Hub's FastAPI backend agents. This is the correct
MCP pattern — tools are execution units, not reasoning units.

**Every tool is non-throwing.**
All external calls are wrapped in try/except. A tool that throws
breaks the entire MCP session. Every tool returns a valid response
object even on failure.

**Tool descriptions are written as policies, not labels.**
Each tool description specifies what it does, when to use it,
and what it returns on failure — not just a one-line label.
This matches the prompt engineering standard applied across every
agent in this portfolio.

---

## Authentication

Every request to `POST /mcp` must include an `X-API-Key` header:

```
X-API-Key: your-secret-key-here
```

The key is compared against the `MCP_API_KEY` environment variable
on the server. Missing or invalid keys return HTTP 401.
`GET /health` requires no authentication.

---

## Rate Limits

`POST /mcp` is limited to **10 requests per IP address per hour**.
Exceeding the limit returns HTTP 429. `GET /health` is not
rate-limited.

**Note:** one search generates 4-5 `/mcp` calls internally (MCP
handshake + one tool call per subtask), so this limit allows
approximately 2 complete Quick searches per hour.

This is a portfolio demonstration server. To remove these limits,
clone the repo and deploy your own instance with your own API keys.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `EXA_API_KEY` | ✅ | Exa AI API key — get one at [exa.ai](https://exa.ai) |
| `MCP_API_KEY` | ✅ | Secret key callers must pass as `X-API-Key` header |
| `CORS_ORIGIN_REGEX` | optional | Regex for allowed origins. Default: `https://.*\.vercel\.app` |

---

## Local Development

```bash
# 1. Clone and enter the repo
git clone https://github.com/Paul-Orlando/web-research-hub-mcp-server.git
cd web-research-hub-mcp-server

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your EXA_API_KEY and MCP_API_KEY

# 5. Run the server
uvicorn main:app --reload
```

Verify it's running:
```bash
curl http://localhost:8000/health
# {"status":"ok","tools":["web_search","fetch_url","calculate","export_report"]}
```

---

## Deployment

### Railway (recommended)

Railway detects the `Procfile` automatically.

1. Push this repo to GitHub
2. New project → Deploy from GitHub repo
3. Root Directory: `/` (not a monorepo)
4. Set `EXA_API_KEY` and `MCP_API_KEY` in the Variables tab
5. Deploy — starts with:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```
6. Settings → Networking → Generate Domain → set Target Port to
   the port shown in deploy logs (typically `8080`)
7. Test: `GET https://your-url.up.railway.app/health`

---

## Connecting to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "web-research-hub": {
      "url": "https://web-production-a8829.up.railway.app/mcp",
      "headers": {
        "X-API-Key": "your-key-here"
      }
    }
  }
}
```

For local development use `http://localhost:8000/mcp` and set
`MCP_API_KEY` in your local `.env`.

---

## Usage Note

This is a portfolio demonstration server with rate limiting and
API key authentication. For production use, clone the repo and
deploy your own instance with your own API keys — the `Procfile`
and Railway deployment instructions above are included for exactly
this purpose.

---

## Roadmap

- [ ] `academic_search` tool — calls the Pinecone Agentic Search
      MCP Server internally, making this server an MCP client of
      another MCP server in this portfolio (three-tier pattern)
- [ ] Source credibility scoring — weight academic/primary sources
      higher than secondary commentary
- [ ] Tool call logging for observability

---

## Related Repos

| Repo | Pattern | Stack |
|---|---|---|
| [web-research-hub](https://github.com/Paul-Orlando/web-research-hub) | Hierarchical 3-Agent Pipeline | Next.js · FastAPI · OpenRouter · Gemini 2.5 Flash · Exa AI |
| [pinecone-mcp-server](https://github.com/Paul-Orlando/pinecone-mcp-server) | Custom MCP Server · Agentic RAG | Node.js · TypeScript · Pinecone · SSE |
| [n8n-mcp-server-agentic-rag](https://github.com/Paul-Orlando/n8n-mcp-server-agentic-rag) | Agentic RAG + MCP Client | Node.js · Express · Pinecone · Gemini Flash 2.5 |

---

## Author

Paul Orlando
Creative Technologist | AI Agent Developer | Data Analytics
🌐 [paulforlando.com](https://www.paulforlando.com) &nbsp;|&nbsp;
💼 [LinkedIn](https://www.linkedin.com/in/paul-orlando-7841b5154) &nbsp;|&nbsp;
🐙 [GitHub](https://github.com/Paul-Orlando)

---

## License

MIT License
