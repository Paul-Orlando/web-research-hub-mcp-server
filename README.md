# web-research-hub-mcp-server

A standalone MCP sidecar for [web-research-hub](https://github.com/Paul-Orlando/web-research-hub). Exposes 4 tools over Streamable HTTP so any MCP-compatible client (Claude Desktop, Claude.ai, custom agents) can call them directly.

---

## Architecture

```
Client (Claude / agent)
        │  POST /mcp  (MCP Streamable HTTP)
        ▼
  FastAPI + FastMCP
        │
  ┌─────┴──────────────────────────────────┐
  │  web_search   fetch_url   calculate   export_report  │
  └─────┬──────────────┬────────────────────┘
        │              │
   Exa AI API      httpx + BS4     ast (stdlib)    fpdf2 / python-docx
```

- Transport: **Streamable HTTP** — clients POST to `/mcp`
- Health check: `GET /health`
- CORS: configurable via `CORS_ORIGIN_REGEX` env var (default: `https://.*\.vercel\.app`)

---

## Tool Reference

### `web_search`
Searches the live web via Exa AI.

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
Fetches a URL and returns clean extracted text.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `url` | string | required | Full URL to fetch |
| `max_length` | int | `5000` | Character limit on returned content |

**Response:**
```json
{ "url": "", "content": "", "title": "", "success": true }
```
Returns `success: false` on failure, never throws.

---

### `calculate`
Evaluates a safe arithmetic expression.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `expression` | string | required | e.g. `"(3 + 4) * 2"` |
| `description` | string | `null` | Optional label for context |

Supported operators: `+  -  *  /  **  %  //`

**Response:**
```json
{ "expression": "(3 + 4) * 2", "result": 14, "description": null }
```
Returns `result: null` with an `error` field on failure, never throws.

---

### `export_report`
Exports a markdown string to PDF, DOCX, or MD, returned as base64.

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `content` | string | required | Markdown source |
| `format` | string | required | `"pdf"`, `"docx"`, or `"md"` |
| `title` | string | `null` | Prepended as H1; used in filename |

Citation links `[text](url)` are rendered as `text (domain.com)` in PDF/DOCX output.

**Response:**
```json
{ "format": "pdf", "filename": "report.pdf", "content_base64": "...", "success": true }
```
Returns `success: false` on failure, never throws.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `EXA_API_KEY` | Yes | Exa AI API key — get one at [exa.ai](https://exa.ai) |
| `CORS_ORIGIN_REGEX` | No | Regex for allowed origins. Default: `https://.*\.vercel\.app` |

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
# Edit .env and add your EXA_API_KEY

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

### Render / Railway (recommended)

Both platforms detect the `Procfile` automatically.

1. Push this repo to GitHub.
2. Create a new **Web Service** pointing to the repo.
3. Set the `EXA_API_KEY` environment variable in the platform dashboard.
4. Deploy — the service starts with:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

### Heroku

```bash
heroku create
heroku config:set EXA_API_KEY=your_key_here
git push heroku main
```

---

## Connecting to Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "web-research-hub": {
      "url": "https://your-deployed-url.com/mcp"
    }
  }
}
```

For local development use `http://localhost:8000/mcp`.
