"""ProductFruits Knowledge Base MCP Server.

Lightweight MCP server for managing Knowledge Base articles
via the ProductFruits REST API.

Endpoints (base: https://api.productfruits.com):
  POST   /v1/knowledgebase/import                                  Import/upsert articles
  GET    /v1/knowledgebase/articles                                 List articles (metadata)
  DELETE /v1/knowledgebase/articles/{correlationId}                  Delete article
  DELETE /v1/knowledgebase/articles/{correlationId}/content/{lang}   Delete language version
  GET    /v1/knowledgebase/categories                               List categories
  GET    /v1/knowledgebase/categories/{correlationId}                Get category
  POST   /v1/knowledgebase/upload-image                             Upload image
"""

import os
import sys
from mcp.server.fastmcp import FastMCP

import httpx

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

API_BASE = "https://api.productfruits.com"
API_KEY = os.environ.get("PRODUCTFRUITS_API_KEY", "")

if not API_KEY:
    print("PRODUCTFRUITS_API_KEY environment variable is required", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

TIMEOUT = 30.0

# ---------------------------------------------------------------------------
# MCP Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "productfruits-kb",
    instructions=(
        "ProductFruits Knowledge Base MCP server. "
        "Use pf_kb_list_articles to see existing articles, "
        "pf_kb_import_article to create/update articles (markdown format), "
        "and pf_kb_list_categories to find category IDs. "
        "Articles support multiple languages. Always set correlationId for upsert behavior."
    ),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, headers=HEADERS, timeout=TIMEOUT)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def pf_kb_list_articles(
    category_correlation_id: str | None = None,
) -> dict:
    """List all Knowledge Base articles with metadata.

    Returns article IDs, correlationIds, category, language variants, and
    publish status. Does NOT return article body content (API limitation).

    Args:
        category_correlation_id: Filter by category. Use 'pf_{id}' for internal
            IDs or custom correlationId. Omit to list all articles.
    """
    params = {}
    if category_correlation_id is not None:
        params["correlationCategoryId"] = category_correlation_id
    with _client() as client:
        resp = client.get("/v1/knowledgebase/articles", params=params)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def pf_kb_import_article(
    title: str,
    content: str,
    language: str = "en",
    correlation_id: str | None = None,
    category_correlation_id: str | None = None,
    slug: str | None = None,
    keywords: str | None = None,
    lead: str | None = None,
    publish: bool = True,
    create_new_version: bool = False,
    is_hidden: bool = False,
) -> dict:
    """Create or update a Knowledge Base article.

    Content must be in Markdown format. Uses upsert semantics: if an article
    with the given correlation_id exists, it updates; otherwise it creates.

    To publish in multiple languages, call this tool once per language with
    the same correlation_id. Each call adds/updates one language variant.

    Args:
        title: Article title.
        content: Article body in Markdown format.
        language: ISO 639-1 language code (e.g., 'en', 'de', 'fr').
        correlation_id: Unique ID for upsert. Use 'pf_{id}' for existing
            articles or any string for new ones. Required for updates.
        category_correlation_id: Category to place article in. Use 'pf_{id}'
            for internal category IDs (e.g., 'pf_15073').
        slug: URL slug. Auto-generated from title if omitted.
        keywords: Comma-separated search keywords.
        lead: Summary excerpt shown in article lists.
        publish: Whether to publish immediately (default: true).
        create_new_version: If true, creates a new version instead of updating
            the existing one. Preserves article history.
        is_hidden: If true, hides article from navigation but keeps it accessible.
    """
    content_obj = {
        "lang": language,
        "title": title,
        "content": content,
        "format": "markdown",
        "publishStatus": "published" if publish else "unpublished",
        "createNewVersion": create_new_version,
    }
    if slug:
        content_obj["slug"] = slug
    if keywords:
        content_obj["keywords"] = keywords
    if lead:
        content_obj["lead"] = lead

    article_obj: dict = {
        "contents": [content_obj],
        "isHidden": is_hidden,
    }
    if correlation_id:
        article_obj["correlationId"] = correlation_id
    if category_correlation_id:
        article_obj["categoryCorrelationId"] = category_correlation_id

    payload = {
        "articles": [article_obj],
        "config": {
            "slugConflictHandling": "auto-number",
            "ignoreImportErrors": False,
            "includeContentInResponse": True,
        },
    }

    with _client() as client:
        resp = client.post("/v1/knowledgebase/import", json=payload)
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def pf_kb_delete_article(correlation_id: str) -> dict:
    """Delete a Knowledge Base article entirely (all languages).

    Args:
        correlation_id: The article's correlationId. Use 'pf_{id}' for
            internal IDs or the custom correlationId set during import.
    """
    with _client() as client:
        resp = client.delete(f"/v1/knowledgebase/articles/{correlation_id}")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def pf_kb_delete_article_language(correlation_id: str, language: str) -> dict:
    """Delete a specific language version of a Knowledge Base article.

    Args:
        correlation_id: The article's correlationId.
        language: ISO 639-1 language code to delete (e.g., 'de').
    """
    with _client() as client:
        resp = client.delete(
            f"/v1/knowledgebase/articles/{correlation_id}/content/{language}"
        )
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def pf_kb_list_categories() -> dict:
    """List all Knowledge Base categories with their IDs, titles, and hierarchy.

    Returns category metadata including EN and DE titles, parent relationships,
    and display order. Use the category ID with 'pf_{id}' prefix as
    category_correlation_id when importing articles.
    """
    with _client() as client:
        resp = client.get("/v1/knowledgebase/categories")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def pf_kb_get_category(correlation_id: str) -> dict:
    """Get details for a specific Knowledge Base category.

    Args:
        correlation_id: Category correlationId. Use 'pf_{id}' for internal IDs.
    """
    with _client() as client:
        resp = client.get(f"/v1/knowledgebase/categories/{correlation_id}")
        resp.raise_for_status()
        return resp.json()


@mcp.tool()
def pf_kb_upload_image(image_path: str) -> dict:
    """Upload an image for use in Knowledge Base articles.

    Returns an image URL that can be embedded in article markdown content
    using standard markdown image syntax: ![alt](url)

    Supported formats: JPG, JPEG, PNG, GIF, WEBP. Max size: 10MB.

    Args:
        image_path: Absolute path to the image file to upload.
    """
    with _client() as client:
        with open(image_path, "rb") as f:
            filename = os.path.basename(image_path)
            upload_headers = {
                "Authorization": f"Bearer {API_KEY}",
            }
            resp = client.post(
                "/v1/knowledgebase/upload-image",
                files={"file": (filename, f)},
                headers=upload_headers,
            )
            resp.raise_for_status()
            return resp.json()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
