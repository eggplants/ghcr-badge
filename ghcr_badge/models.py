"""Pydantic models of the Docker Registry HTTP API V2 responses.

Docker Image Manifest V2-2 and OCI Image Manifest V1 are structurally identical
as far as this package is concerned, so a single pair of models covers both:

- `ImageManifest` for `manifest.v2+json` / `oci.image.manifest.v1+json`
- `ImageIndex` for `manifest.list.v2+json` / `oci.image.index.v1+json`

See:
https://docs.docker.com/registry/spec/manifest-v2-2/#manifest-list-field-descriptions
https://github.com/opencontainers/image-spec/blob/main/manifest.md
https://github.com/opencontainers/image-spec/blob/main/image-index.md
https://github.com/opencontainers/image-spec/blob/main/descriptor.md
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

_ATTESTATION_REFERENCE_TYPE = "attestation-manifest"
_UNKNOWN_PLATFORM = "unknown"


class _Base(BaseModel):
    """Base model tolerating unknown fields the registry may add."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


class Platform(_Base):
    """Platform an image index descriptor refers to."""

    architecture: str
    os: str
    variant: str | None = None
    os_version: str | None = Field(default=None, alias="os.version")
    os_features: list[str] | None = Field(default=None, alias="os.features")
    features: list[str] | None = None

    @property
    def is_unknown(self) -> bool:
        """Whether this platform is the `unknown/unknown` placeholder.

        Returns:
        -------
        bool
            True if neither os nor architecture is a real platform.

        """
        return _UNKNOWN_PLATFORM in (self.os, self.architecture)


class Descriptor(_Base):
    """OCI content descriptor.

    Used for a manifest's `config` and `layers`, and for an index's `manifests`.
    `platform` and `annotations` are only populated in the index case.
    """

    mediaType: str  # noqa: N815
    digest: str
    size: int
    urls: list[str] | None = None
    annotations: dict[str, str] | None = None
    platform: Platform | None = None
    artifactType: str | None = None  # noqa: N815

    @property
    def is_attestation(self) -> bool:
        """Whether this descriptor points at an attestation rather than an image.

        Attestation manifests are attached to an index by buildx alongside the
        real per-platform images. They carry a `unknown/unknown` platform and
        weigh a few hundred bytes, so treating one as the image yields a
        nonsense size badge.

        Returns:
        -------
        bool
            True if this descriptor is an attestation manifest.

        """
        annotations = self.annotations or {}
        if annotations.get("vnd.docker.reference.type") == _ATTESTATION_REFERENCE_TYPE:
            return True
        return self.platform is not None and self.platform.is_unknown


class ImageManifest(_Base):
    """Image Manifest V2-2 / OCI Image Manifest V1."""

    schemaVersion: int  # noqa: N815
    mediaType: str | None = None  # noqa: N815
    config: Descriptor
    layers: list[Descriptor] = Field(default_factory=list)
    annotations: dict[str, str] | None = None
    subject: Descriptor | None = None
    artifactType: str | None = None  # noqa: N815

    @property
    def total_size(self) -> int:
        """Total size of the config blob and every layer, in bytes.

        Returns:
        -------
        int
            Sum of the config size and all layer sizes.

        """
        return self.config.size + sum(layer.size for layer in self.layers)


class ImageIndex(_Base):
    """Manifest List V2-2 / OCI Image Index V1."""

    schemaVersion: int  # noqa: N815
    mediaType: str | None = None  # noqa: N815
    manifests: list[Descriptor] = Field(default_factory=list)
    annotations: dict[str, str] | None = None

    def pick_image_descriptor(self) -> Descriptor | None:
        """Pick the descriptor of an actual image, skipping attestations.

        Returns:
        -------
        Descriptor | None
            First non-attestation descriptor, or None if the index is empty.
            Falls back to the first descriptor when every entry looks like an
            attestation, so a badge is still rendered.

        """
        if not self.manifests:
            return None
        for descriptor in self.manifests:
            if not descriptor.is_attestation:
                return descriptor
        return self.manifests[0]


class TagList(_Base):
    """Response of `/v2/<name>/tags/list`."""

    name: str | None = None
    tags: list[str] = Field(default_factory=list)


class RegistryError(_Base):
    """A single error entry returned by the registry."""

    code: str | None = None
    message: str | None = None


class ErrorResponse(_Base):
    """Error response of the registry API."""

    errors: list[RegistryError] = Field(default_factory=list)

    def describe(self) -> str:
        """Render the errors as a single human-readable string.

        Returns:
        -------
        str
            Comma-separated `CODE: message` pairs.

        """
        return ", ".join(f"{e.code}: {e.message}" for e in self.errors)
