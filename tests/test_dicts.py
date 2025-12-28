"""Tests for ghcr_badge.dicts module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from ghcr_badge.dicts import (
        ManifestListV2,
        ManifestV2,
        OCIImageIndexV1,
        OCIImageManifestV1,
    )


class TestManifestV2:
    """Test ManifestV2 TypedDict."""

    def test_manifest_v2_structure(self) -> None:
        """Test ManifestV2 structure."""
        from ghcr_badge.dicts import ManifestV2

        manifest: ManifestV2 = {
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

        assert manifest["mediaType"] == "application/vnd.docker.distribution.manifest.v2+json"
        assert manifest["schemaVersion"] == 2
        assert manifest["config"]["size"] == 1000
        assert len(manifest["layers"]) == 1


class TestManifestListV2:
    """Test ManifestListV2 TypedDict."""

    def test_manifest_list_v2_structure(self) -> None:
        """Test ManifestListV2 structure."""
        from ghcr_badge.dicts import ManifestListV2

        manifest_list: ManifestListV2 = {
            "mediaType": "application/vnd.docker.distribution.manifest.list.v2+json",
            "schemaVersion": 2,
            "manifests": [
                {
                    "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                    "size": 3000,
                    "digest": "sha256:ghi789",
                },
            ],
        }

        assert manifest_list["mediaType"] == "application/vnd.docker.distribution.manifest.list.v2+json"
        assert manifest_list["schemaVersion"] == 2
        assert len(manifest_list["manifests"]) == 1


class TestOCIImageManifestV1:
    """Test OCIImageManifestV1 TypedDict."""

    def test_oci_image_manifest_v1_structure(self) -> None:
        """Test OCIImageManifestV1 structure."""
        from ghcr_badge.dicts import OCIImageManifestV1

        manifest: OCIImageManifestV1 = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.manifest.v1+json",
            "config": {
                "mediaType": "application/vnd.oci.image.config.v1+json",
                "size": 1500,
                "digest": "sha256:jkl012",
            },
            "layers": [
                {
                    "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
                    "size": 2500,
                    "digest": "sha256:mno345",
                },
            ],
            "annotations": {"org.opencontainers.image.created": "2024-01-01T00:00:00Z"},
        }

        assert manifest["mediaType"] == "application/vnd.oci.image.manifest.v1+json"
        assert manifest["schemaVersion"] == 2
        assert manifest["config"]["size"] == 1500
        assert len(manifest["layers"]) == 1
        assert "org.opencontainers.image.created" in manifest["annotations"]


class TestOCIImageIndexV1:
    """Test OCIImageIndexV1 TypedDict."""

    def test_oci_image_index_v1_structure(self) -> None:
        """Test OCIImageIndexV1 structure."""
        from ghcr_badge.dicts import OCIImageIndexV1

        index: OCIImageIndexV1 = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "manifests": [
                {
                    "mediaType": "application/vnd.oci.image.manifest.v1+json",
                    "size": 4000,
                    "digest": "sha256:pqr678",
                },
            ],
        }

        assert index["mediaType"] == "application/vnd.oci.image.index.v1+json"
        assert index["schemaVersion"] == 2
        assert len(index["manifests"]) == 1
