"""Define TypedDict classes of Image Manifest (V2-2) and OCI Image Manifest (V1).

See:
https://docs.docker.com/registry/spec/manifest-v2-2/#manifest-list-field-descriptions
https://github.com/opencontainers/image-spec/blob/main/manifest.md
"""

from __future__ import annotations

from typing import TypedDict


class _ManifestV2Layer(TypedDict):
    mediaType: str
    digest: str
    size: int


class ManifestV2(TypedDict):
    """Image Manifest V2."""

    mediaType: str
    schemaVersion: int
    config: _ManifestV2Layer
    layers: list[_ManifestV2Layer]


class ManifestListV2(TypedDict):
    """Manifest List V2."""

    mediaType: str
    schemaVersion: int
    manifests: list[_ManifestV2Layer]


class _OCIImageManifestV1Config(TypedDict):
    mediaType: str
    size: int
    digest: str


class _OCIImageManifestV1Layer(TypedDict):
    mediaType: str
    size: int
    digest: str


class OCIImageManifestV1(TypedDict):
    """Manifest V1 for OCI Image."""

    schemaVersion: int
    mediaType: str
    config: _OCIImageManifestV1Config
    layers: list[_OCIImageManifestV1Layer]
    annotations: dict[str, str]


class OCIImageIndexV1(TypedDict):
    """Index V1 for OCI Image."""

    schemaVersion: int
    mediaType: str
    manifests: list[OCIImageManifestV1]
