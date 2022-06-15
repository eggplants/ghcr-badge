from __future__ import annotations

from typing import TypedDict


class ManifestV2(TypedDict):
    mediaType: str
    schemaVersion: int
    config: ManifestV2Layer
    layers: list[ManifestV2Layer]


class ManifestV2Layer(TypedDict):
    mediaType: str
    digest: str
    size: int


class ManifestListV2(TypedDict):
    mediaType: str
    schemaVersion: int
    maifests: list[ManifestV2Layer]


class ManifestListV2Layer(TypedDict):
    mediaType: str
    digest: str
    size: int
    platform: ManifestListV2Platform


class ManifestListV2Platform(TypedDict):
    architecture: str
    os: str
