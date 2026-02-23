"""Tests for ProductFruits KB MCP server.

Uses unittest.mock to intercept httpx calls. No live API access required.
Set PRODUCTFRUITS_API_KEY in the environment before running (any value works).

    PRODUCTFRUITS_API_KEY=test uv run --with "mcp[cli]" --with httpx pytest tests/
"""

import json
import os

# Must set before importing server (it exits without the key)
os.environ.setdefault("PRODUCTFRUITS_API_KEY", "test-key-for-ci")

from unittest.mock import MagicMock, patch

import httpx
import pytest

import server


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _mock_response(data: dict | list, status_code: int = 200) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


@pytest.fixture()
def mock_client():
    """Patch _client() to return a mock httpx.Client."""
    client = MagicMock(spec=httpx.Client)
    client.__enter__ = MagicMock(return_value=client)
    client.__exit__ = MagicMock(return_value=False)
    with patch.object(server, "_client", return_value=client):
        yield client


# ---------------------------------------------------------------------------
# pf_kb_list_articles
# ---------------------------------------------------------------------------


class TestListArticles:
    def test_list_all(self, mock_client):
        articles = [{"id": 1, "correlationId": "art-1"}]
        mock_client.get.return_value = _mock_response(articles)

        result = server.pf_kb_list_articles()

        mock_client.get.assert_called_once_with(
            "/v1/knowledgebase/articles", params={}
        )
        assert result == articles

    def test_filter_by_category(self, mock_client):
        mock_client.get.return_value = _mock_response([])

        server.pf_kb_list_articles(category_correlation_id="pf_15073")

        mock_client.get.assert_called_once_with(
            "/v1/knowledgebase/articles",
            params={"correlationCategoryId": "pf_15073"},
        )

    def test_raises_on_http_error(self, mock_client):
        resp = _mock_response({})
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=resp
        )
        mock_client.get.return_value = resp

        with pytest.raises(httpx.HTTPStatusError):
            server.pf_kb_list_articles()


# ---------------------------------------------------------------------------
# pf_kb_import_article
# ---------------------------------------------------------------------------


class TestImportArticle:
    def test_minimal_payload(self, mock_client):
        mock_client.post.return_value = _mock_response({"imported": 1})

        server.pf_kb_import_article(title="Test", content="# Hello")

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/knowledgebase/import"
        payload = call_args[1]["json"]

        article = payload["articles"][0]
        content_obj = article["contents"][0]

        assert content_obj["title"] == "Test"
        assert content_obj["content"] == "# Hello"
        assert content_obj["lang"] == "en"
        assert content_obj["format"] == "markdown"
        assert content_obj["publishStatus"] == "published"
        assert content_obj["createNewVersion"] is False
        assert "slug" not in content_obj
        assert "keywords" not in content_obj
        assert "lead" not in content_obj
        assert "correlationId" not in article
        assert "categoryCorrelationId" not in article
        assert article["isHidden"] is False

    def test_full_payload(self, mock_client):
        mock_client.post.return_value = _mock_response({"imported": 1})

        server.pf_kb_import_article(
            title="SSO Setup",
            content="## Overview\n\nGuide...",
            language="de",
            correlation_id="sso-setup",
            category_correlation_id="pf_15073",
            slug="sso-einrichten",
            keywords="SSO, SAML",
            lead="SSO einrichten.",
            publish=False,
            create_new_version=True,
            is_hidden=True,
        )

        payload = mock_client.post.call_args[1]["json"]
        article = payload["articles"][0]
        content_obj = article["contents"][0]

        assert content_obj["lang"] == "de"
        assert content_obj["slug"] == "sso-einrichten"
        assert content_obj["keywords"] == "SSO, SAML"
        assert content_obj["lead"] == "SSO einrichten."
        assert content_obj["publishStatus"] == "unpublished"
        assert content_obj["createNewVersion"] is True
        assert article["correlationId"] == "sso-setup"
        assert article["categoryCorrelationId"] == "pf_15073"
        assert article["isHidden"] is True

    def test_config_defaults(self, mock_client):
        mock_client.post.return_value = _mock_response({})

        server.pf_kb_import_article(title="T", content="C")

        payload = mock_client.post.call_args[1]["json"]
        config = payload["config"]

        assert config["slugConflictHandling"] == "auto-number"
        assert config["ignoreImportErrors"] is False
        assert config["includeContentInResponse"] is True


# ---------------------------------------------------------------------------
# pf_kb_delete_article
# ---------------------------------------------------------------------------


class TestDeleteArticle:
    def test_delete_by_correlation_id(self, mock_client):
        mock_client.delete.return_value = _mock_response({"deleted": True})

        result = server.pf_kb_delete_article("sso-setup")

        mock_client.delete.assert_called_once_with(
            "/v1/knowledgebase/articles/sso-setup"
        )
        assert result == {"deleted": True}

    def test_delete_with_pf_prefix(self, mock_client):
        mock_client.delete.return_value = _mock_response({})

        server.pf_kb_delete_article("pf_95735")

        mock_client.delete.assert_called_once_with(
            "/v1/knowledgebase/articles/pf_95735"
        )


# ---------------------------------------------------------------------------
# pf_kb_delete_article_language
# ---------------------------------------------------------------------------


class TestDeleteArticleLanguage:
    def test_delete_language(self, mock_client):
        mock_client.delete.return_value = _mock_response({"deleted": True})

        result = server.pf_kb_delete_article_language("sso-setup", "de")

        mock_client.delete.assert_called_once_with(
            "/v1/knowledgebase/articles/sso-setup/content/de"
        )
        assert result == {"deleted": True}


# ---------------------------------------------------------------------------
# pf_kb_list_categories
# ---------------------------------------------------------------------------


class TestListCategories:
    def test_list(self, mock_client):
        cats = [{"id": 1, "title": "DCO"}]
        mock_client.get.return_value = _mock_response(cats)

        result = server.pf_kb_list_categories()

        mock_client.get.assert_called_once_with("/v1/knowledgebase/categories")
        assert result == cats


# ---------------------------------------------------------------------------
# pf_kb_get_category
# ---------------------------------------------------------------------------


class TestGetCategory:
    def test_get(self, mock_client):
        cat = {"id": 15073, "title": "DCO"}
        mock_client.get.return_value = _mock_response(cat)

        result = server.pf_kb_get_category("pf_15073")

        mock_client.get.assert_called_once_with(
            "/v1/knowledgebase/categories/pf_15073"
        )
        assert result == cat


# ---------------------------------------------------------------------------
# pf_kb_upload_image
# ---------------------------------------------------------------------------


class TestUploadImage:
    def test_upload(self, mock_client, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG\r\n\x1a\n")  # minimal PNG header

        mock_client.post.return_value = _mock_response(
            {"imageUrl": "https://cdn-assets.productfruits.com/abc.png"}
        )

        result = server.pf_kb_upload_image(str(img))

        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/knowledgebase/upload-image"
        assert "files" in call_args[1]
        assert result["imageUrl"].startswith("https://cdn-assets.productfruits.com/")


# ---------------------------------------------------------------------------
# Config / module-level
# ---------------------------------------------------------------------------


class TestConfig:
    def test_api_base(self):
        assert server.API_BASE == "https://api.productfruits.com"

    def test_headers_contain_auth(self):
        assert "Authorization" in server.HEADERS
        assert server.HEADERS["Authorization"].startswith("Bearer ")

    def test_timeout_is_reasonable(self):
        assert 10 <= server.TIMEOUT <= 120

    def test_mcp_server_name(self):
        assert server.mcp.name == "productfruits-kb"
