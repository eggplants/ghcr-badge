from __future__ import annotations

import base64
import fnmatch
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
    def __init__(
        self, color: str = "#44cc11", ignore_tag: str = "latest", trim_type: str = ""
    ) -> None:
        self.color = color
        self.ignore_tags: list[str] = ignore_tag.split(",")
        self.trim_pattern = {
            "patch": r"^v?\d+\.\d+\.\d+[^.]*$",
            "major": r"^v?\d+\.\d+[^.]*$",
        }.get(trim_type, "^$")

    def generate_tags(
        self,
        package_owner: str,
        package_name: str,
        n: int = 10,
        label: str = "image tags",
    ) -> str:
        if n < 0:
            raise ValueError(f"{n} should be positive.")
        try:
            tags = self.filter_tags(package_owner, package_name)[::-1][:n][::-1]
        except InvalidTagListError:
            return self.get_invalid_badge(label)
        badge = anybadge.Badge(
            label=label, value=" | ".join(tags), default_color=self.color
        )
        return str(badge.badge_svg_text)

    def generate_latest_tag(
        self, package_owner: str, package_name: str, label: str = "version"
    ) -> str:
        try:
            latest_tag = self.filter_tags(package_owner, package_name)[-1]
        except InvalidTagListError:
            return self.get_invalid_badge(label)
        badge = anybadge.Badge(
            label=label, value=str(latest_tag), default_color=self.color
        )
        return str(badge.badge_svg_text)

    def generate_develop_tag(
        self, package_owner: str, package_name: str, label: str = "version"
    ) -> str:
        try:
            tags = [
                tag
                for tag in self.get_tags(package_owner, package_name)
                if tag != "latest"
            ]
            if "develop" not in tags or tags.index("develop") + 1 == len(tags):
                return self.get_invalid_badge(label)
            develop_tag = tags[tags.index("develop") + 1]
        except InvalidTagListError:
            return self.get_invalid_badge(label)
        badge = anybadge.Badge(
            label=label, value=str(develop_tag), default_color=self.color
        )
        return str(badge.badge_svg_text)

    def generate_size(
        self,
        package_owner: str,
        package_name: str,
        tag: str = "latest",
        label: str = "image size",
    ) -> str:
        try:
            manifest = self.get_manifest(package_owner, package_name, tag)
        except InvalidManifestError:
            return self.get_invalid_badge(label)
        config_size = int(manifest.get("config", {"size": 0}).get("size", 0))
        layer_size = sum(
            int(layer.get("size", 0)) for layer in manifest.get("layers", [])
        )
        size = f"{config_size + layer_size}B"
        badge = anybadge.Badge(
            label=label,
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

    def filter_tags(self, package_owner: str, package_name: str) -> list[str]:
        tags: list[str] = []
        target_tags = [
            t
            for t in self.get_tags(package_owner, package_name)
            if not re.match(self.trim_pattern, t)
        ]
        for tag in target_tags:
            matched = False
            for ignore_tag in self.ignore_tags:
                if fnmatch.fnmatch(tag, ignore_tag):
                    matched = True
                    break
            if not matched:
                tags.append(tag)
        return tags

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
        token = base64.b64encode(f"v1:{package_owner}/{package_name}:0".encode())
        return token.decode("utf-8")
