"""Generate badge."""

from __future__ import annotations

import base64
import fnmatch
import re
from typing import TYPE_CHECKING, cast

import requests
from anybadge import Badge  # type: ignore[import,unused-ignore]
from humanfriendly import format_size, parse_size

from .dicts import ManifestListV2, ManifestV2, OCIImageIndexV1, OCIImageManifestV1

if TYPE_CHECKING:
    from typing_extensions import Self

_TIMEOUT = 10

# force to cast badge value into str
Badge.value_type = str


class InvalidTokenError(Exception):
    """Exception for invalid token."""


class InvalidTagError(Exception):
    """Exception for invalid tag."""


class InvalidTagListError(Exception):
    """Exception for invalid tag list."""


class InvalidManifestError(Exception):
    """Exception for invalid manifest."""


class InvalidImageError(Exception):
    """Exception for invalid image."""


class InvalidMediaTypeError(Exception):
    """Exception for invalid media type."""


_GITHUB_USER_PATTERN = r"^[a-zA-Z0-9]([a-zA-Z0-9]?|[-]?([a-zA-Z0-9])){0,38}$"
_GITHUB_REPO_PATTERN = r"^[-a-zA-Z0-9]{1,100}$"
_IMAGE_TAG_PATTERN = r"^([a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}|sha256:[a-z0-9]{64})$"
_USER_AGENT = "Docker-Client/20.10.2 (linux)"

_MEDIA_TYPE_MANIFEST = "application/vnd.docker.distribution.manifest"
_MEDIA_TYPE_MANIFEST_V2 = f"{_MEDIA_TYPE_MANIFEST}.v2+json"
_MEDIA_TYPE_MANIFEST_LIST_V2 = f"{_MEDIA_TYPE_MANIFEST}.list.v2+json"

_MEDIA_TYPE_OCI_IMAGE_MANIFEST = "application/vnd.oci.image.manifest"
_MEDIA_TYPE_OCI_IMAGE_MANIFEST_V1 = f"{_MEDIA_TYPE_OCI_IMAGE_MANIFEST}.v1+json"
_MEDIA_TYPE_OCI_IMAGE_INDEX_V1 = "application/vnd.oci.image.index.v1+json"


class GHCRBadgeGenerator:
    """Generator for GHCR Badge."""

    def __init__(
        self: Self,
        *,
        color: str = "#44cc11",
        ignore_tag: str = "latest",
        trim_type: str = "",
    ) -> None:
        """_summary_.

        Parameters
        ----------
        self : Self
            class instance
        color : str, optional
            badge color, by default "#44cc11"
        ignore_tag : str, optional
            tag name to hide, by default "latest"
        trim_type : str, optional
            type to hide tags

        """
        self.color = color
        self.ignore_tags: list[str] = ignore_tag.split(",")
        self.trim_pattern = {
            "patch": r"^v?\d+\.\d+\.\d+[^.]*$",
            "major": r"^v?\d+\.\d+[^.]*$",
        }.get(trim_type, "^$")

    def generate_tags(
        self: Self,
        package_owner: str,
        package_name: str,
        *,
        n: int = 10,
        label: str = "image tags",
    ) -> str:
        """Generate badge of package tags.

        Parameters
        ----------
        self : Self
            class instance
        package_owner : str
            package owner name
        package_name : str
            package_name
        n : int, optional
            number of displayed tags, by default 10
        label : str, optional
            label text, by default "image tags"

        Returns
        -------
        str
            svg string of generated badge of package tags

        Raises
        ------
        ValueError
            raise if number of displayed tags is invalid

        """
        if n < 0:
            msg = f"{n} should be positive."
            raise ValueError(msg)
        try:
            tags = self.filter_tags(package_owner, package_name)[::-1][:n][::-1]
        except InvalidTagListError:
            return self.get_invalid_badge(label)
        badge_value = " " + " | ".join(tags)
        badge = Badge(
            label=label,
            value=badge_value,
            default_color=self.color,
        )
        return str(badge.badge_svg_text)

    def generate_latest_tag(
        self: Self,
        package_owner: str,
        package_name: str,
        *,
        label: str = "version",
    ) -> str:
        """Generate latest tag badge.

        Parameters
        ----------
        self : Self
            class instance
        package_owner : str
            package owner name
        package_name : str
            package name
        label : str, optional
            label text, by default "version"

        Returns
        -------
        str
            svg string of generated badge of latest tag

        """
        try:
            latest_tag = self.filter_tags(package_owner, package_name)[-1]
        except InvalidTagListError:
            return self.get_invalid_badge(label)
        badge_value = str(latest_tag)
        badge = Badge(
            label=label,
            value=badge_value,
            default_color=self.color,
        )
        return str(badge.badge_svg_text)

    def generate_size(
        self: Self,
        package_owner: str,
        package_name: str,
        tag: str = "latest",
        label: str = "image size",
    ) -> str:
        """Generate image size badge.

        Parameters
        ----------
        self : Self
            class instance
        package_owner : str
            package owner name
        package_name : str
            package name
        tag : str, optional
            tag name, by default "latest"
        label : str, optional
            label text, by default "image size"

        Returns
        -------
        str
            svg string of generated badge of size

        """
        try:
            manifest = self.get_manifest(package_owner, package_name, tag=tag)
        except (InvalidManifestError, InvalidMediaTypeError):
            return self.get_invalid_badge(label)
        config_size = int(manifest.get("config", {"size": 0}).get("size", 0))
        layers = [int(layer.get("size", 0)) for layer in manifest.get("layers", [])]
        layer_size = sum(layers)
        size = f"{config_size + layer_size}B"
        badge = Badge(
            label=label,
            value=format_size(parse_size(size), binary=True),
            default_color=self.color,
        )
        return str(badge.badge_svg_text)

    def get_manifest(
        self: Self,
        package_owner: str,
        package_name: str,
        *,
        tag: str = "latest",
    ) -> ManifestV2 | OCIImageManifestV1:
        """Get manifest from ghcr api.

        Parameters
        ----------
        self : Self
            class instance
        package_owner : str
            package owner name
        package_name : str
            package name
        tag : str, optional
            tag name, by default "latest"

        Returns
        -------
        ManifestV2
            dict containing returned manifest information

        Raises
        ------
        InvalidTagError
            raise if response contains invalid tag
        InvalidManifestError
            raise if response is invalid manifest
        InvalidMediaTypeError
            raise if response is invalid media type

        """
        if re.match(_IMAGE_TAG_PATTERN, tag) is None:
            raise InvalidTagError(tag)

        token = self.__auth(package_owner, package_name)
        url = f"https://ghcr.io/v2/{package_owner}/{package_name}/manifests/{tag}"
        manifest = requests.get(
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Authorization": f"Bearer {token}",
                "Accept": f"{_MEDIA_TYPE_OCI_IMAGE_INDEX_V1}, {_MEDIA_TYPE_OCI_IMAGE_MANIFEST_V1}",
            },
            timeout=_TIMEOUT,
        ).json()

        if manifest is None:
            msg = "manifest is empty."
            raise InvalidManifestError(msg)

        if "errors" in manifest:
            msg = f"manifest contains some error: {manifest.get('errors')}"
            raise InvalidManifestError(msg)

        media_type = manifest.get("mediaType")

        if media_type == _MEDIA_TYPE_MANIFEST_V2:
            return cast(ManifestV2, manifest)

        if media_type == _MEDIA_TYPE_OCI_IMAGE_MANIFEST_V1:
            return cast(OCIImageManifestV1, manifest)

        if media_type == _MEDIA_TYPE_MANIFEST_LIST_V2:
            manifest = cast(ManifestListV2, manifest)
            manifests = manifest.get("manifests")
            if not isinstance(manifests, list) or len(manifests) == 0:
                msg = "Returned list of manifest is empty."
                raise InvalidManifestError(msg)
            if (digest := manifests[0].get("digest")) is None:
                msg = f"Digest of a manifest is empty:\n{manifests[0]}"
                raise InvalidManifestError(msg)
            return self.get_manifest(package_owner, package_name, tag=digest)

        if media_type == _MEDIA_TYPE_OCI_IMAGE_INDEX_V1:
            manifest = cast(OCIImageIndexV1, manifest)
            manifests = manifest.get("manifests")
            if not isinstance(manifests, list) or len(manifests) == 0:
                msg = "Returned list of manifest is empty."
                raise InvalidManifestError(msg)
            if (digest := manifests[0].get("digest")) is None:
                msg = f"Digest of a manifest is empty:\n{manifests[0]}"
                raise InvalidManifestError(msg)
            return self.get_manifest(package_owner, package_name, tag=digest)

        raise InvalidMediaTypeError(media_type)

    def get_tags(self: Self, package_owner: str, package_name: str) -> list[str]:
        """Get tags of the given package.

        Parameters
        ----------
        self : Self
            class instance
        package_owner : str
            package owner name
        package_name : str
            package name

        Returns
        -------
        list[str]
            tags, e.g. '1.0.0'

        Raises
        ------
        InvalidTagListError
            raise if response is invalid

        """
        token = self.__auth(package_owner, package_name)
        url = f"https://ghcr.io/v2/{package_owner}/{package_name}/tags/list"
        tags = (
            requests.get(
                url,
                headers={"User-Agent": _USER_AGENT, "Authorization": f"Bearer {token}"},
                timeout=10,
            )
            .json()
            .get("tags")
        )
        if not isinstance(tags, list) or len(tags) == 0:
            raise InvalidTagListError
        return [str(tag) for tag in tags]

    def filter_tags(self: Self, package_owner: str, package_name: str) -> list[str]:
        """Filter tags by regex pattern.

        Parameters
        ----------
        package_owner : str
            package owner name
        package_name : str
            package name

        Returns
        -------
        list[str]
            Filtered tags

        """
        tags: list[str] = []
        target_tags = [t for t in self.get_tags(package_owner, package_name) if not re.match(self.trim_pattern, t)]
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
        """Generate and Get invalid badge.

        Parameters
        ----------
        label : str
            badge label

        Returns
        -------
        str
            svg string

        """
        badge = Badge(label=label, value="invalid", default_color="#e05d44")
        return str(badge.badge_svg_text)

    @staticmethod
    def __auth(package_owner: str, package_name: str) -> str:
        m_user = re.match(_GITHUB_USER_PATTERN, package_owner)
        m_repo = re.match(_GITHUB_REPO_PATTERN, package_owner)
        if m_user is None or m_repo is None:
            raise InvalidImageError
        token = base64.b64encode(f"v1:{package_owner}/{package_name}:0".encode())
        return token.decode("utf-8")
