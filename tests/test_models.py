"""Tests for ghcr_badge.models module.

The shapes asserted here were captured from real ghcr.io responses.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ghcr_badge.models import (
    Descriptor,
    ErrorResponse,
    ImageIndex,
    ImageManifest,
    Platform,
    TagList,
)

_DIGEST = "sha256:" + "0" * 64


def _descriptor(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "mediaType": "application/vnd.oci.image.manifest.v1+json",
        "digest": _DIGEST,
        "size": 673,
    }
    base.update(overrides)
    return base


class TestPlatform:
    """Test Platform model."""

    def test_minimal(self) -> None:
        """Only architecture and os are guaranteed to be present."""
        platform = Platform.model_validate({"architecture": "amd64", "os": "linux"})
        assert platform.variant is None
        assert not platform.is_unknown

    def test_variant(self) -> None:
        """Arm descriptors carry a variant."""
        platform = Platform.model_validate({"architecture": "arm", "os": "linux", "variant": "v7"})
        assert platform.variant == "v7"

    def test_dotted_aliases(self) -> None:
        """`os.version` and `os.features` are spec fields with dots in the name."""
        platform = Platform.model_validate(
            {
                "architecture": "amd64",
                "os": "windows",
                "os.version": "10.0.17763.1234",
                "os.features": ["win32k"],
            },
        )
        assert platform.os_version == "10.0.17763.1234"
        assert platform.os_features == ["win32k"]

    @pytest.mark.parametrize(
        ("architecture", "os_"),
        [("unknown", "unknown"), ("unknown", "linux"), ("amd64", "unknown")],
    )
    def test_is_unknown(self, architecture: str, os_: str) -> None:
        """A placeholder platform is detected from either field."""
        assert Platform.model_validate({"architecture": architecture, "os": os_}).is_unknown

    def test_missing_required(self) -> None:
        """architecture and os are required."""
        with pytest.raises(ValidationError):
            Platform.model_validate({"os": "linux"})


class TestDescriptor:
    """Test Descriptor model."""

    def test_minimal(self) -> None:
        """A config/layer descriptor has no platform or annotations."""
        descriptor = Descriptor.model_validate(_descriptor())
        assert descriptor.size == 673
        assert descriptor.platform is None
        assert not descriptor.is_attestation

    def test_attestation_by_annotation(self) -> None:
        """buildx marks attestations with a reference type annotation."""
        descriptor = Descriptor.model_validate(
            _descriptor(annotations={"vnd.docker.reference.type": "attestation-manifest"}),
        )
        assert descriptor.is_attestation

    def test_attestation_by_unknown_platform(self) -> None:
        """An unknown/unknown platform also marks a non-image descriptor."""
        descriptor = Descriptor.model_validate(
            _descriptor(platform={"architecture": "unknown", "os": "unknown"}),
        )
        assert descriptor.is_attestation

    def test_real_image_is_not_attestation(self) -> None:
        """A normal per-platform descriptor is kept."""
        descriptor = Descriptor.model_validate(
            _descriptor(platform={"architecture": "amd64", "os": "linux"}),
        )
        assert not descriptor.is_attestation

    def test_missing_required(self) -> None:
        """mediaType, digest and size are required."""
        with pytest.raises(ValidationError):
            Descriptor.model_validate({"mediaType": "application/vnd.oci.image.manifest.v1+json"})

    def test_extra_fields_ignored(self) -> None:
        """Unknown fields must not break parsing, so new spec fields are safe."""
        descriptor = Descriptor.model_validate(_descriptor(somethingNew="x"))
        assert descriptor.digest == _DIGEST


class TestImageManifest:
    """Test ImageManifest model."""

    def test_total_size(self) -> None:
        """total_size sums the config blob and every layer."""
        manifest = ImageManifest.model_validate(
            {
                "schemaVersion": 2,
                "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
                "config": _descriptor(size=1000),
                "layers": [_descriptor(size=2000), _descriptor(size=3000)],
            },
        )
        assert manifest.total_size == 6000

    def test_annotations_optional(self) -> None:
        """Real ghcr.io OCI manifests frequently omit annotations."""
        manifest = ImageManifest.model_validate(
            {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "config": _descriptor(size=1000),
                "layers": [_descriptor(size=2000)],
            },
        )
        assert manifest.annotations is None
        assert manifest.total_size == 3000

    def test_config_required(self) -> None:
        """A manifest without a config blob is not usable."""
        with pytest.raises(ValidationError):
            ImageManifest.model_validate({"schemaVersion": 2, "layers": []})

    def test_no_layers(self) -> None:
        """A manifest with no layers still reports the config size."""
        manifest = ImageManifest.model_validate({"schemaVersion": 2, "config": _descriptor(size=1000)})
        assert manifest.total_size == 1000


class TestImageIndex:
    """Test ImageIndex model."""

    def test_pick_skips_attestations(self) -> None:
        """The first real image wins over a leading attestation."""
        index = ImageIndex.model_validate(
            {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [
                    _descriptor(
                        digest="sha256:" + "a" * 64,
                        platform={"architecture": "unknown", "os": "unknown"},
                        annotations={"vnd.docker.reference.type": "attestation-manifest"},
                    ),
                    _descriptor(digest="sha256:" + "b" * 64, platform={"architecture": "amd64", "os": "linux"}),
                ],
            },
        )
        picked = index.pick_image_descriptor()
        assert picked is not None
        assert picked.digest == "sha256:" + "b" * 64

    def test_pick_empty(self) -> None:
        """An empty index yields nothing to resolve."""
        index = ImageIndex.model_validate({"schemaVersion": 2, "manifests": []})
        assert index.pick_image_descriptor() is None

    def test_pick_falls_back_when_all_attestations(self) -> None:
        """Rather than fail, fall back to the first descriptor."""
        index = ImageIndex.model_validate(
            {
                "schemaVersion": 2,
                "manifests": [
                    _descriptor(digest="sha256:" + "a" * 64, platform={"architecture": "unknown", "os": "unknown"}),
                ],
            },
        )
        picked = index.pick_image_descriptor()
        assert picked is not None
        assert picked.digest == "sha256:" + "a" * 64

    def test_mixed_media_types(self) -> None:
        """An index may mix OCI and Docker descriptors, as ghcr.io really does."""
        index = ImageIndex.model_validate(
            {
                "schemaVersion": 2,
                "mediaType": "application/vnd.oci.image.index.v1+json",
                "manifests": [
                    _descriptor(
                        mediaType="application/vnd.docker.distribution.manifest.v2+json",
                        platform={"architecture": "amd64", "os": "linux"},
                    ),
                    _descriptor(platform={"architecture": "arm64", "os": "linux"}),
                ],
            },
        )
        assert len(index.manifests) == 2


class TestTagList:
    """Test TagList model."""

    def test_parse(self) -> None:
        """tags/list returns the repository name alongside the tags."""
        tag_list = TagList.model_validate({"name": "eggplants/ghcr-badge", "tags": ["v1.0.0", "latest"]})
        assert tag_list.tags == ["v1.0.0", "latest"]

    def test_empty(self) -> None:
        """A missing tags key parses to an empty list."""
        assert TagList.model_validate({"name": "x"}).tags == []


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_describe(self) -> None:
        """Registry errors are rendered for the exception message."""
        error = ErrorResponse.model_validate(
            {"errors": [{"code": "MANIFEST_UNKNOWN", "message": "manifest unknown"}]},
        )
        assert error.describe() == "MANIFEST_UNKNOWN: manifest unknown"

    def test_multiple(self) -> None:
        """Multiple errors are joined."""
        error = ErrorResponse.model_validate(
            {"errors": [{"code": "A", "message": "a"}, {"code": "B", "message": "b"}]},
        )
        assert error.describe() == "A: a, B: b"
