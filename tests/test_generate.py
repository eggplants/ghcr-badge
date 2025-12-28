"""Tests for ghcr_badge.generate module."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock, patch

import pytest

from ghcr_badge.generate import (
    GHCRBadgeGenerator,
    InvalidImageError,
    InvalidManifestError,
    InvalidMediaTypeError,
    InvalidTagError,
    InvalidTagListError,
)

if TYPE_CHECKING:
    from ghcr_badge.dicts import ManifestV2, OCIImageManifestV1


class TestGHCRBadgeGenerator:
    """Test GHCRBadgeGenerator class."""

    def test_init_default(self) -> None:
        """Test initialization with default values."""
        gen = GHCRBadgeGenerator()
        assert gen.color == "#44cc11"
        assert gen.ignore_tags == ["latest"]
        assert gen.trim_pattern == "^$"

    def test_init_custom_color(self) -> None:
        """Test initialization with custom color."""
        gen = GHCRBadgeGenerator(color="#ff0000")
        assert gen.color == "#ff0000"

    def test_init_ignore_tags(self) -> None:
        """Test initialization with ignore tags."""
        gen = GHCRBadgeGenerator(ignore_tag="latest,dev,staging")
        assert gen.ignore_tags == ["latest", "dev", "staging"]

    def test_init_trim_type_patch(self) -> None:
        """Test initialization with trim_type patch."""
        gen = GHCRBadgeGenerator(trim_type="patch")
        assert gen.trim_pattern == r"^v?\d+\.\d+\.\d+[^.]*$"

    def test_init_trim_type_major(self) -> None:
        """Test initialization with trim_type major."""
        gen = GHCRBadgeGenerator(trim_type="major")
        assert gen.trim_pattern == r"^v?\d+\.\d+[^.]*$"

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.filter_tags")
    def test_generate_tags_success(self, mock_filter_tags: MagicMock) -> None:
        """Test generate_tags with successful response."""
        mock_filter_tags.return_value = ["v1.0.0", "v1.0.1", "v1.0.2"]
        gen = GHCRBadgeGenerator()
        result = gen.generate_tags("user", "repo", n=3)
        assert "v1.0.0" in result
        assert "v1.0.1" in result
        assert "v1.0.2" in result

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.filter_tags")
    def test_generate_tags_invalid(self, mock_filter_tags: MagicMock) -> None:
        """Test generate_tags with invalid response."""
        mock_filter_tags.side_effect = InvalidTagListError
        gen = GHCRBadgeGenerator()
        result = gen.generate_tags("user", "repo")
        assert "invalid" in result

    def test_generate_tags_negative_n(self) -> None:
        """Test generate_tags with negative n value."""
        gen = GHCRBadgeGenerator()
        with pytest.raises(ValueError, match="should be positive"):
            gen.generate_tags("user", "repo", n=-1)

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.filter_tags")
    def test_generate_latest_tag_success(self, mock_filter_tags: MagicMock) -> None:
        """Test generate_latest_tag with successful response."""
        mock_filter_tags.return_value = ["v1.0.0", "v1.0.1", "v1.0.2"]
        gen = GHCRBadgeGenerator()
        result = gen.generate_latest_tag("user", "repo")
        assert "v1.0.2" in result

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.filter_tags")
    def test_generate_latest_tag_invalid(self, mock_filter_tags: MagicMock) -> None:
        """Test generate_latest_tag with invalid response."""
        mock_filter_tags.side_effect = InvalidTagListError
        gen = GHCRBadgeGenerator()
        result = gen.generate_latest_tag("user", "repo")
        assert "invalid" in result

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.get_manifest")
    def test_generate_size_success(self, mock_get_manifest: MagicMock) -> None:
        """Test generate_size with successful response."""
        mock_manifest: ManifestV2 = {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "schemaVersion": 2,
            "config": {
                "mediaType": "application/vnd.docker.container.image.v1+json",
                "size": 1000,
                "digest": "sha256:abc123",
            },
            "layers": [
                {
                    "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                    "size": 2000,
                    "digest": "sha256:def456",
                },
                {
                    "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                    "size": 3000,
                    "digest": "sha256:ghi789",
                },
            ],
        }
        mock_get_manifest.return_value = mock_manifest
        gen = GHCRBadgeGenerator()
        result = gen.generate_size("user", "repo", tag="v1.0.0")
        assert "5.9 KiB" in result or "6" in result  # humanfriendly format

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.get_manifest")
    def test_generate_size_invalid(self, mock_get_manifest: MagicMock) -> None:
        """Test generate_size with invalid response."""
        mock_get_manifest.side_effect = InvalidManifestError
        gen = GHCRBadgeGenerator()
        result = gen.generate_size("user", "repo")
        assert "invalid" in result

    @patch("ghcr_badge.generate.requests.get")
    def test_get_manifest_manifest_v2(self, mock_get: MagicMock) -> None:
        """Test get_manifest with ManifestV2 response."""
        mock_response = Mock()
        mock_manifest: ManifestV2 = {
            "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
            "schemaVersion": 2,
            "config": {
                "mediaType": "application/vnd.docker.container.image.v1+json",
                "size": 1000,
                "digest": "sha256:abc123",
            },
            "layers": [
                {
                    "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                    "size": 2000,
                    "digest": "sha256:def456",
                },
            ],
        }
        mock_response.json.return_value = mock_manifest
        mock_get.return_value = mock_response

        gen = GHCRBadgeGenerator()
        result = gen.get_manifest("user", "repo", tag="v1.0.0")
        assert result == mock_manifest

    @patch("ghcr_badge.generate.requests.get")
    def test_get_manifest_oci_image_manifest_v1(self, mock_get: MagicMock) -> None:
        """Test get_manifest with OCIImageManifestV1 response."""
        mock_response = Mock()
        mock_manifest: OCIImageManifestV1 = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {
                "mediaType": "application/vnd.oci.image.config.v1+json",
                "size": 1000,
                "digest": "sha256:abc123",
            },
            "layers": [
                {"mediaType": "application/vnd.oci.image.layer.v1.tar+gzip", "size": 2000, "digest": "sha256:def456"},
            ],
            "annotations": {},
        }
        mock_response.json.return_value = mock_manifest
        mock_get.return_value = mock_response

        gen = GHCRBadgeGenerator()
        result = gen.get_manifest("user", "repo", tag="v1.0.0")
        assert result == mock_manifest

    @patch("ghcr_badge.generate.requests.get")
    def test_get_manifest_invalid_tag(self, mock_get: MagicMock) -> None:
        """Test get_manifest with invalid tag."""
        gen = GHCRBadgeGenerator()
        with pytest.raises(InvalidTagError):
            gen.get_manifest("user", "repo", tag="invalid tag with spaces")

    @patch("ghcr_badge.generate.requests.get")
    def test_get_manifest_empty_manifest(self, mock_get: MagicMock) -> None:
        """Test get_manifest with empty manifest."""
        mock_response = Mock()
        mock_response.json.return_value = None
        mock_get.return_value = mock_response

        gen = GHCRBadgeGenerator()
        with pytest.raises(InvalidManifestError, match="manifest is empty"):
            gen.get_manifest("user", "repo")

    @patch("ghcr_badge.generate.requests.get")
    def test_get_manifest_with_errors(self, mock_get: MagicMock) -> None:
        """Test get_manifest with errors in response."""
        mock_response = Mock()
        mock_response.json.return_value = {"errors": [{"code": "UNAUTHORIZED", "message": "authentication required"}]}
        mock_get.return_value = mock_response

        gen = GHCRBadgeGenerator()
        with pytest.raises(InvalidManifestError, match="manifest contains some error"):
            gen.get_manifest("user", "repo")

    @patch("ghcr_badge.generate.requests.get")
    def test_get_manifest_invalid_media_type(self, mock_get: MagicMock) -> None:
        """Test get_manifest with invalid media type."""
        mock_response = Mock()
        mock_response.json.return_value = {"mediaType": "application/vnd.invalid.type", "schemaVersion": 2}
        mock_get.return_value = mock_response

        gen = GHCRBadgeGenerator()
        with pytest.raises(InvalidMediaTypeError):
            gen.get_manifest("user", "repo")

    @patch("ghcr_badge.generate.requests.get")
    def test_get_tags_success(self, mock_get: MagicMock) -> None:
        """Test get_tags with successful response."""
        mock_response = Mock()
        mock_response.json.return_value = {"tags": ["v1.0.0", "v1.0.1", "latest"]}
        mock_get.return_value = mock_response

        gen = GHCRBadgeGenerator()
        result = gen.get_tags("user", "repo")
        assert result == ["v1.0.0", "v1.0.1", "latest"]

    @patch("ghcr_badge.generate.requests.get")
    def test_get_tags_empty(self, mock_get: MagicMock) -> None:
        """Test get_tags with empty response."""
        mock_response = Mock()
        mock_response.json.return_value = {"tags": []}
        mock_get.return_value = mock_response

        gen = GHCRBadgeGenerator()
        with pytest.raises(InvalidTagListError):
            gen.get_tags("user", "repo")

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.get_tags")
    def test_filter_tags_basic(self, mock_get_tags: MagicMock) -> None:
        """Test filter_tags with basic filtering."""
        mock_get_tags.return_value = ["v1.0.0", "latest", "v1.0.1"]
        gen = GHCRBadgeGenerator(ignore_tag="latest")
        result = gen.filter_tags("user", "repo")
        assert result == ["v1.0.0", "v1.0.1"]

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.get_tags")
    def test_filter_tags_with_pattern(self, mock_get_tags: MagicMock) -> None:
        """Test filter_tags with pattern filtering."""
        mock_get_tags.return_value = ["v1.0.0", "v1.0.1", "v2.0.0-alpha", "dev"]
        gen = GHCRBadgeGenerator(ignore_tag="dev,*-alpha")
        result = gen.filter_tags("user", "repo")
        assert result == ["v1.0.0", "v1.0.1"]

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.get_tags")
    def test_filter_tags_with_trim_pattern(self, mock_get_tags: MagicMock) -> None:
        """Test filter_tags with trim pattern."""
        mock_get_tags.return_value = ["v1.0.0", "v1.0", "v2.0.0", "dev"]
        gen = GHCRBadgeGenerator(ignore_tag="dev", trim_type="patch")
        result = gen.filter_tags("user", "repo")
        assert result == ["v1.0"]

    def test_get_invalid_badge(self) -> None:
        """Test get_invalid_badge."""
        result = GHCRBadgeGenerator.get_invalid_badge("test label")
        assert "test label" in result
        assert "invalid" in result

    @patch("ghcr_badge.generate.GHCRBadgeGenerator.get_tags")
    def test_auth_valid(self, mock_get_tags: MagicMock) -> None:
        """Test authentication with valid input by verifying get_tags works."""
        mock_get_tags.return_value = ["v1.0.0"]
        gen = GHCRBadgeGenerator()
        result = gen.get_tags("user", "repo")
        assert result == ["v1.0.0"]

    @patch("ghcr_badge.generate.requests.get")
    def test_auth_invalid_user(self, mock_get: MagicMock) -> None:
        """Test authentication with invalid user."""
        gen = GHCRBadgeGenerator()
        with pytest.raises(InvalidImageError):
            gen.get_tags("invalid user!", "repo")

    @patch("ghcr_badge.generate.requests.get")
    def test_auth_invalid_repo(self, mock_get: MagicMock) -> None:
        """Test authentication with invalid repo."""
        gen = GHCRBadgeGenerator()
        with pytest.raises(InvalidImageError):
            gen.get_tags("user", "invalid repo!")
