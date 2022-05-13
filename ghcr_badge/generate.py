from __future__ import annotations

import re
from typing import TypedDict, cast

import anybadge  # type: ignore[import]
import requests
from humanfriendly import format_size, parse_size


class InvalidTokenError(Exception):
    pass


class InvalidTagError(Exception):
    pass


class InvalidTagListError(Exception):
    pass


class InvalidManifestError(Exception):
    pass


class InvalidImageError(Exception):
    pass


class Manifest(TypedDict):
    mediaType: str
    schemaVersion: int
    config: Layer
    layers: list[Layer]


class Layer(TypedDict):
    mediaType: str
    digest: str
    size: int


_GITHUB_USER_PATTERN = r"^[a-zA-Z0-9]([a-zA-Z0-9]?|[-]?([a-zA-Z0-9])){0,38}$"
_GITHUB_REPO_PATTERN = r"^[-a-zA-Z0-9]{1,100}$"
_IMAGE_TAG_PATTERN = r"^[a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}$"
_USER_AGENT = "Docker-Client/20.10.2 (linux)"


class GHCRBadgeGenerator:
    def __init__(self, color: str = "#44cc11", ignore_tag: str = "latest") -> None:
        self.color = color
        self.ignore_tags: list[str] = ignore_tag.split(",")

    def generate_latest_tag(self, package_owner: str, package_name: str) -> str:
        try:
            tags = [
                tag
                for tag in self.get_tags(package_owner, package_name)
                if tag not in self.ignore_tags
            ]
            latest_tag = tags[-1]
        except InvalidTagListError:
            return self.get_invalid_badge("version")
        badge = anybadge.Badge(
            label="version", value=str(latest_tag), default_color=self.color
        )
        return str(badge.badge_svg_text)

    def generate_tags(self, package_owner: str, package_name: str, n: int = 10) -> str:
        if n < 0:
            raise ValueError(f"{n} should be positive.")
        try:
            tags = [
                tag
                for tag in self.get_tags(package_owner, package_name)
                if tag not in self.ignore_tags
            ][::-1][:n][::-1]
        except InvalidTagListError:
            return self.get_invalid_badge("image tags")
        badge = anybadge.Badge(
            label="image tags", value=" | ".join(tags), default_color=self.color
        )
        return str(badge.badge_svg_text)

    def generate_size(
        self, package_owner: str, package_name: str, tag: str = "latest"
    ) -> str:
        try:
            manifest = self.get_manifest(package_owner, package_name, tag)
        except InvalidManifestError:
            return self.get_invalid_badge("image size")
        config_size = int(manifest.get("config", {"size": 0}).get("size", 0))
        layer_size = sum(
            int(layer.get("size", 0)) for layer in manifest.get("layers", [])
        )
        size = f"{config_size + layer_size}B"
        badge = anybadge.Badge(
            label="image size",
            value=format_size(parse_size(size), binary=True),
            default_color=self.color,
        )
        return str(badge.badge_svg_text)

    def get_manifest(
        self, package_owner: str, package_name: str, tag: str = "latest"
    ) -> Manifest:
        m0 = re.match(_IMAGE_TAG_PATTERN, tag)
        if m0 is None:
            raise InvalidTagError
        token = self.__auth(package_owner, package_name)
        url = f"https://ghcr.io/v2/{package_owner}/{package_name}/manifests/{tag}"
        manifest = requests.get(
            url, headers={"User-Agent": _USER_AGENT, "Authorization": f"Bearer {token}"}
        ).json()
        if manifest is None or "errors" in manifest:
            raise InvalidManifestError(str(manifest.get("errors")))
        return cast(Manifest, manifest)

    def get_tags(self, package_owner: str, package_name: str) -> list[str]:
        token = self.__auth(package_owner, package_name)
        url = f"https://ghcr.io/v2/{package_owner}/{package_name}/tags/list"
        tags = (
            requests.get(
                url,
                headers={"User-Agent": _USER_AGENT, "Authorization": f"Bearer {token}"},
            )
            .json()
            .get("tags")
        )
        if not isinstance(tags, list) or len(tags) == 0:
            raise InvalidTagListError
        return [str(tag) for tag in tags]

    @staticmethod
    def get_invalid_badge(label: str) -> str:
        badge = anybadge.Badge(label=label, value="invalid", default_color="#e05d44")
        return str(badge.badge_svg_text)

    @staticmethod
    def __auth(package_owner: str, package_name: str) -> str:
        m1 = re.match(_GITHUB_USER_PATTERN, package_owner)
        m2 = re.match(_GITHUB_REPO_PATTERN, package_owner)
        if m1 is None or m2 is None:
            raise InvalidImageError
        auth_url = f"https://ghcr.io/token?scope=repository:{package_owner}/{package_name}:pull"
        token = (
            requests.get(auth_url, headers={"User-Agent": _USER_AGENT})
            .json()
            .get("token")
        )
        if token is None:
            raise InvalidTokenError
        return str(token)
