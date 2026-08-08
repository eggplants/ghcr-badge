"""Tests for ghcr_badge.server module."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from ghcr_badge.server import app, return_svg


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


class TestReturnSvg:
    """Test return_svg function."""

    def test_return_svg_basic(self) -> None:
        """Test return_svg with basic SVG content."""
        svg_content = "<svg><text>Test Badge</text></svg>"
        response = return_svg(svg_content)

        assert response.status_code == 200
        assert response.media_type == "image/svg+xml"
        assert bytes(response.body).decode() == svg_content

    def test_return_svg_headers(self) -> None:
        """Test return_svg response headers."""
        svg_content = "<svg><text>Test Badge</text></svg>"
        response = return_svg(svg_content)

        assert "Cache-Control" in response.headers
        assert "Pragma" in response.headers
        assert "Expires" in response.headers
        assert response.headers["Pragma"] == "no-cache"


class TestIndexRoute:
    """Test index route."""

    def test_get_index_html(self, client: TestClient) -> None:
        """Test GET / returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text

    def test_get_index_html_explicit(self, client: TestClient) -> None:
        """Test GET /index.html returns HTML."""
        response = client.get("/index.html")
        assert response.status_code == 200
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text

    def test_get_index_json(self, client: TestClient) -> None:
        """Test GET /index.json returns JSON."""
        response = client.get("/index.json")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        data = response.json()
        assert "available_paths" in data


class TestHealthRoute:
    """Test health route."""

    def test_health(self, client: TestClient) -> None:
        """Test GET /health returns OK."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.text == "OK"


class TestHeadRequests:
    """Test that GET routes also answer HEAD, as Flask used to."""

    @pytest.mark.parametrize("path", ["/", "/index", "/index.html", "/index.json", "/health"])
    def test_head_static_routes(self, client: TestClient, path: str) -> None:
        """Test HEAD on the non-badge routes."""
        assert client.head(path).status_code == 200

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_head_badge_route(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test HEAD on a badge route."""
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg><text>v1.0.0</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.head("/testuser/testrepo/tags")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"


class TestStaticFiles:
    """Test mounted static files."""

    def test_get_favicon(self, client: TestClient) -> None:
        """Test GET /static/favicon.ico is served."""
        response = client.get("/static/favicon.ico")
        assert response.status_code == 200


class TestTagsRoute:
    """Test tags route."""

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_tags_default(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET /<owner>/<name>/tags with default parameters."""
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg><text>v1.0.0 | v1.0.1</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/tags")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        mock_generator.generate_tags.assert_called_once_with("testuser", "testrepo", n=3, label="image tags")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_tags_with_parameters(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET /<owner>/<name>/tags with custom parameters."""
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg><text>v1.0.0</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/tags?color=red&n=5&ignore=dev&label=versions&trim=patch")
        assert response.status_code == 200
        mock_generator_class.assert_called_once_with(color="red", ignore_tag="dev", trim_type="patch")
        mock_generator.generate_tags.assert_called_once_with("testuser", "testrepo", n=5, label="versions")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_tags_nested_path(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET with nested package path."""
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg><text>tag</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/nested/path/repo/tags")
        assert response.status_code == 200
        mock_generator.generate_tags.assert_called_once_with("testuser", "nested/path/repo", n=3, label="image tags")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_tags_generator_error(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET tags reports a generator failure as JSON."""
        mock_generator_class.side_effect = ValueError("boom")

        response = client.get("/testuser/testrepo/tags")
        assert response.status_code == 200
        assert response.json() == {"exception": "ValueError", "message": "boom"}


class TestLatestTagRoute:
    """Test latest_tag route."""

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_latest_tag_default(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET /<owner>/<name>/latest_tag with default parameters."""
        mock_generator = Mock()
        mock_generator.generate_latest_tag.return_value = "<svg><text>v1.0.2</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/latest_tag")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        mock_generator.generate_latest_tag.assert_called_once_with("testuser", "testrepo", label="version")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_latest_tag_with_parameters(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET /<owner>/<name>/latest_tag with custom parameters."""
        mock_generator = Mock()
        mock_generator.generate_latest_tag.return_value = "<svg><text>v2.0.0</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/latest_tag?color=blue&ignore=alpha&label=release&trim=major")
        assert response.status_code == 200
        mock_generator_class.assert_called_once_with(color="blue", ignore_tag="alpha", trim_type="major")
        mock_generator.generate_latest_tag.assert_called_once_with("testuser", "testrepo", label="release")


class TestSizeRoute:
    """Test size route."""

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_size_default(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET /<owner>/<name>/size with default parameters."""
        mock_generator = Mock()
        mock_generator.generate_size.return_value = "<svg><text>10 MB</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/size")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        mock_generator.generate_size.assert_called_once_with("testuser", "testrepo", tag="latest", label="image size")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_size_with_parameters(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET /<owner>/<name>/size with custom parameters."""
        mock_generator = Mock()
        mock_generator.generate_size.return_value = "<svg><text>15 MB</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/size?tag=v1.0.0&color=green&label=size")
        assert response.status_code == 200
        mock_generator_class.assert_called_once_with(color="green", trim_type="")
        mock_generator.generate_size.assert_called_once_with("testuser", "testrepo", tag="v1.0.0", label="size")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_size_nested_path(self, mock_generator_class: MagicMock, client: TestClient) -> None:
        """Test GET size with nested package path."""
        mock_generator = Mock()
        mock_generator.generate_size.return_value = "<svg><text>20 MB</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/org/repo/size")
        assert response.status_code == 200
        mock_generator.generate_size.assert_called_once_with("testuser", "org/repo", tag="latest", label="image size")


class TestMain:
    """Test main function."""

    @patch("ghcr_badge.server.uvicorn.run")
    @patch("ghcr_badge.server.environ.get")
    def test_main_default_port(self, mock_environ_get: MagicMock, mock_run: MagicMock) -> None:
        """Test main function with default port."""
        from ghcr_badge.server import main

        mock_environ_get.side_effect = lambda key, default: default  # noqa: ARG005

        main()

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["port"] == 5000

    @patch("ghcr_badge.server.uvicorn.run")
    @patch("ghcr_badge.server.environ.get")
    def test_main_custom_port(self, mock_environ_get: MagicMock, mock_run: MagicMock) -> None:
        """Test main function with custom port from environment."""
        from ghcr_badge.server import main

        mock_environ_get.return_value = "3000"

        main()

        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs["port"] == 3000
