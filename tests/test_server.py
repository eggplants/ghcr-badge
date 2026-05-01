"""Tests for ghcr_badge.server module."""

from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from flask.testing import FlaskClient

from ghcr_badge.server import app, return_svg


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestReturnSvg:
    """Test return_svg function."""

    def test_return_svg_basic(self) -> None:
        """Test return_svg with basic SVG content."""
        svg_content = "<svg><text>Test Badge</text></svg>"
        with app.app_context():
            response = return_svg(svg_content)

            assert response.status_code == 200
            assert response.mimetype == "image/svg+xml"
            assert response.data.decode() == svg_content

    def test_return_svg_headers(self) -> None:
        """Test return_svg response headers."""
        svg_content = "<svg><text>Test Badge</text></svg>"
        with app.app_context():
            response = return_svg(svg_content)

            assert "Cache-Control" in response.headers
            assert "Pragma" in response.headers
            assert "Expires" in response.headers
            assert response.headers["Pragma"] == "no-cache"


class TestIndexRoute:
    """Test index route."""

    def test_get_index_html(self, client: FlaskClient) -> None:
        """Test GET / returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_get_index_html_explicit(self, client: FlaskClient) -> None:
        """Test GET /index.html returns HTML."""
        response = client.get("/index.html")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_get_index_json(self, client: FlaskClient) -> None:
        """Test GET /index.json returns JSON."""
        response = client.get("/index.json")
        assert response.status_code == 200
        assert response.content_type == "application/json"
        data = response.get_json()
        assert "available_paths" in data
        assert any("/pulls" in path for path in data["available_paths"])


class TestTagsRoute:
    """Test tags route."""

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_tags_default(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET /<owner>/<name>/tags with default parameters."""
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg><text>v1.0.0 | v1.0.1</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/tags")
        assert response.status_code == 200
        assert response.mimetype == "image/svg+xml"
        mock_generator.generate_tags.assert_called_once_with("testuser", "testrepo", n=3, label="image tags")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_tags_with_parameters(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET /<owner>/<name>/tags with custom parameters."""
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg><text>v1.0.0</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/tags?color=red&n=5&ignore=dev&label=versions&trim=patch")
        assert response.status_code == 200
        mock_generator_class.assert_called_once_with(color="red", ignore_tag="dev", trim_type="patch")
        mock_generator.generate_tags.assert_called_once_with("testuser", "testrepo", n=5, label="versions")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_tags_nested_path(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET with nested package path."""
        mock_generator = Mock()
        mock_generator.generate_tags.return_value = "<svg><text>tag</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/nested/path/repo/tags")
        assert response.status_code == 200
        mock_generator.generate_tags.assert_called_once_with("testuser", "nested/path/repo", n=3, label="image tags")


class TestLatestTagRoute:
    """Test latest_tag route."""

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_latest_tag_default(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET /<owner>/<name>/latest_tag with default parameters."""
        mock_generator = Mock()
        mock_generator.generate_latest_tag.return_value = "<svg><text>v1.0.2</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/latest_tag")
        assert response.status_code == 200
        assert response.mimetype == "image/svg+xml"
        mock_generator.generate_latest_tag.assert_called_once_with("testuser", "testrepo", label="version")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_latest_tag_with_parameters(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
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
    def test_get_size_default(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET /<owner>/<name>/size with default parameters."""
        mock_generator = Mock()
        mock_generator.generate_size.return_value = "<svg><text>10 MB</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/size")
        assert response.status_code == 200
        assert response.mimetype == "image/svg+xml"
        mock_generator.generate_size.assert_called_once_with("testuser", "testrepo", tag="latest", label="image size")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_size_with_parameters(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET /<owner>/<name>/size with custom parameters."""
        mock_generator = Mock()
        mock_generator.generate_size.return_value = "<svg><text>15 MB</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/size?tag=v1.0.0&color=green&label=size")
        assert response.status_code == 200
        mock_generator_class.assert_called_once_with(color="green", trim_type="")
        mock_generator.generate_size.assert_called_once_with("testuser", "testrepo", tag="v1.0.0", label="size")

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_size_nested_path(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET size with nested package path."""
        mock_generator = Mock()
        mock_generator.generate_size.return_value = "<svg><text>20 MB</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/org/repo/size")
        assert response.status_code == 200
        mock_generator.generate_size.assert_called_once_with("testuser", "org/repo", tag="latest", label="image size")


class TestPullsRoute:
    """Test pulls route."""

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_pulls_default(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET /<owner>/<name>/pulls with default parameters."""
        mock_generator = Mock()
        mock_generator.generate_pulls.return_value = "<svg><text>1.2K</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/pulls")
        assert response.status_code == 200
        assert response.mimetype == "image/svg+xml"
        mock_generator_class.assert_called_once_with(color="#44cc11")
        mock_generator.generate_pulls.assert_called_once_with(
            "testuser",
            "testrepo",
            label="pulls",
        )

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_pulls_with_parameters(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET /<owner>/<name>/pulls with custom parameters."""
        mock_generator = Mock()
        mock_generator.generate_pulls.return_value = "<svg><text>3.4K</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/testrepo/pulls?color=blue&label=container%20pulls")
        assert response.status_code == 200
        mock_generator_class.assert_called_once_with(color="blue")
        mock_generator.generate_pulls.assert_called_once_with(
            "testuser",
            "testrepo",
            label="container pulls",
        )

    @patch("ghcr_badge.server.GHCRBadgeGenerator")
    def test_get_pulls_nested_path(self, mock_generator_class: MagicMock, client: FlaskClient) -> None:
        """Test GET pulls with nested package path."""
        mock_generator = Mock()
        mock_generator.generate_pulls.return_value = "<svg><text>9</text></svg>"
        mock_generator_class.return_value = mock_generator

        response = client.get("/testuser/nested/path/repo/pulls")
        assert response.status_code == 200
        mock_generator.generate_pulls.assert_called_once_with(
            "testuser",
            "nested/path/repo",
            label="pulls",
        )


class TestMain:
    """Test main function."""

    @patch("ghcr_badge.server.serve")
    @patch("ghcr_badge.server.environ.get")
    def test_main_default_port(self, mock_environ_get: MagicMock, mock_serve: MagicMock) -> None:
        """Test main function with default port."""
        from ghcr_badge.server import main

        mock_environ_get.side_effect = lambda key, default: default

        main()

        mock_serve.assert_called_once()
        call_kwargs = mock_serve.call_args[1]
        assert call_kwargs["port"] == 5000

    @patch("ghcr_badge.server.serve")
    @patch("ghcr_badge.server.environ.get")
    def test_main_custom_port(self, mock_environ_get: MagicMock, mock_serve: MagicMock) -> None:
        """Test main function with custom port from environment."""
        from ghcr_badge.server import main

        mock_environ_get.return_value = "3000"

        main()

        mock_serve.assert_called_once()
        call_kwargs = mock_serve.call_args[1]
        assert call_kwargs["port"] == 3000
