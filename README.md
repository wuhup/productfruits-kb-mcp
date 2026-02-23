# ProductFruits Knowledge Base MCP Server

Lightweight [MCP](https://modelcontextprotocol.io/) server for managing Knowledge Base articles via the [ProductFruits REST API](https://help.productfruits.com/en/article/knowledge-base-api-quickstart).

Built with [FastMCP](https://github.com/jlowin/fastmcp) and [httpx](https://www.python-httpx.org/).

## Tools

| Tool | Description |
|------|-------------|
| `pf_kb_list_articles` | List articles with metadata (filterable by category) |
| `pf_kb_import_article` | Create or update an article (upsert via `correlation_id`) |
| `pf_kb_delete_article` | Delete an article entirely |
| `pf_kb_delete_article_language` | Delete a specific language version |
| `pf_kb_list_categories` | List all categories with hierarchy |
| `pf_kb_get_category` | Get details for a specific category |
| `pf_kb_upload_image` | Upload an image, returns a hosted URL for embedding |

## Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) (Python package runner)
- A ProductFruits API key with Knowledge Base permissions

### Register with Claude Code

```bash
claude mcp add productfruits -s user \
  -e PRODUCTFRUITS_API_KEY=<YOUR_API_KEY> \
  -- uv run --with "mcp[cli]" --with httpx \
  <path-to-server.py>
```

Replace `<YOUR_API_KEY>` with your ProductFruits Bearer token and `<path-to-server.py>` with the absolute path to `server.py`.

### Verify

```bash
claude mcp list          # Should show "productfruits" with 7 tools
```

## Usage

### List existing articles

```
pf_kb_list_articles()
pf_kb_list_articles(category_correlation_id="pf_15073")
```

### Create an article

```
pf_kb_import_article(
    title="How to Configure SSO",
    content="## Overview\n\nStep-by-step guide...",
    language="en",
    correlation_id="sso-configuration",
    category_correlation_id="pf_15073",
    keywords="SSO, SAML, authentication",
    lead="Learn how to set up SSO.",
)
```

Content is **Markdown** format. The API converts it to HTML for display.

### Multilingual articles

Call `pf_kb_import_article` once per language with the same `correlation_id`:

```
# English version
pf_kb_import_article(title="SSO Setup", content="...", language="en", correlation_id="sso-setup")

# German version (updates the same article)
pf_kb_import_article(title="SSO einrichten", content="...", language="de", correlation_id="sso-setup")
```

### Delete an article

```
pf_kb_delete_article("sso-configuration")                  # All languages
pf_kb_delete_article_language("sso-configuration", "de")    # German only
```

### Upload an image

```
pf_kb_upload_image("/path/to/screenshot.png")
# Returns: {"imageId": "...", "imageUrl": "https://cdn-assets.productfruits.com/..."}
```

Embed in markdown: `![Alt text](https://cdn-assets.productfruits.com/...)`

## Key Concepts

**correlation_id** enables upsert behavior. If an article with that ID exists, it updates; otherwise it creates. For existing articles without a custom ID, use `pf_{articleId}` (e.g., `pf_95735`).

**category_correlation_id** places an article in a category. Use `pf_{categoryId}` format for internal IDs. Call `pf_kb_list_categories()` to find available categories.

**The list endpoint returns metadata only.** Article body content is not available via the API. Keep your source content stored separately if you need to edit later.

## API Reference

Base URL: `https://api.productfruits.com`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/knowledgebase/articles` | List articles |
| POST | `/v1/knowledgebase/import` | Import/upsert articles |
| DELETE | `/v1/knowledgebase/articles/{correlationId}` | Delete article |
| DELETE | `/v1/knowledgebase/articles/{correlationId}/content/{lang}` | Delete language version |
| GET | `/v1/knowledgebase/categories` | List categories |
| GET | `/v1/knowledgebase/categories/{correlationId}` | Get category |
| POST | `/v1/knowledgebase/upload-image` | Upload image |

## Documentation

- [KB API Quickstart](https://help.productfruits.com/en/article/knowledge-base-api-quickstart)
- [Import Articles](https://help.productfruits.com/en/article/knowledge-base-api-import-articles-endpoint)
- [List Articles](https://help.productfruits.com/en/article/knowledge-base-api-list-articles-endpoint)
- [Delete Article](https://help.productfruits.com/en/article/knowledge-base-api-delete-article-endpoint)
- [Delete by Language](https://help.productfruits.com/en/article/knowledge-base-api-delete-article--by-language-endpoint)
- [Upload Images](https://help.productfruits.com/en/article/knowledge-base-api-upload-images-endpoint)
- [Import Categories](https://help.productfruits.com/en/article/knowledge-base-api-import-categories)

## License

MIT — see [LICENSE](LICENSE).
