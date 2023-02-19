"""Define objects of Image Manifest V 2, Schema 2 by TypedDict.

See:
https://docs.docker.com/registry/spec/manifest-v2-2/#manifest-list-field-descriptions
"""

from __future__ import annotations

from typing import TypedDict


class ManifestV2(TypedDict):
    """Image Manifest root."""

    mediaType: str  # noqa: N815
    schemaVersion: int  # noqa: N815
    config: ManifestV2Layer
    layers: list[ManifestV2Layer]


class ManifestV2Layer(TypedDict):
    """Fields of an item in the layers list."""

    mediaType: str  # noqa: N815
    digest: str
    size: int


class ManifestListV2(TypedDict):
    """The manifests field contains a list of manifests."""

    mediaType: str  # noqa: N815
    schemaVersion: int  # noqa: N815
    manifests: list[ManifestV2Layer]


class ManifestListV2Layer(TypedDict):
    """The manifests field contains a list of manifests."""

    mediaType: str  # noqa: N815
    digest: str
    size: int
    platform: ManifestListV2Platform


class ManifestListV2Platform(TypedDict):
    """The platform object describes the platform."""

    architecture: str
    os: str
