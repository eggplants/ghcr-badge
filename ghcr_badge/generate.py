"""Generate badge."""

from __future__ import annotations

import base64
import fnmatch
import re
from typing import TYPE_CHECKING, TypeVar

import requests
from anybadge import Badge  # type: ignore[import,unused-ignore]
from humanfriendly import format_size, parse_size
from pydantic import BaseModel, ValidationError

from .models import ErrorResponse, ImageIndex, ImageManifest, TagList

if TYPE_CHECKING:
    from typing_extensions import Self

_TIMEOUT = 10
_MAX_INDEX_DEPTH = 4


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
_GITHUB_REPO_PATTERN = r"^[-a-zA-Z0-9]{1,100}(?:/[-a-zA-Z0-9]{1,100})*$"
_IMAGE_TAG_PATTERN = r"^([a-zA-Z0-9_][a-zA-Z0-9_.-]{0,127}|sha256:[a-z0-9]{64})$"
_USER_AGENT = "Docker-Client/20.10.2 (linux)"

_MEDIA_TYPE_MANIFEST = "application/vnd.docker.distribution.manifest"
_MEDIA_TYPE_MANIFEST_V2 = f"{_MEDIA_TYPE_MANIFEST}.v2+json"
_MEDIA_TYPE_MANIFEST_LIST_V2 = f"{_MEDIA_TYPE_MANIFEST}.list.v2+json"

_MEDIA_TYPE_OCI_IMAGE_MANIFEST = "application/vnd.oci.image.manifest"
_MEDIA_TYPE_OCI_IMAGE_MANIFEST_V1 = f"{_MEDIA_TYPE_OCI_IMAGE_MANIFEST}.v1+json"
_MEDIA_TYPE_OCI_IMAGE_INDEX_V1 = "application/vnd.oci.image.index.v1+json"

# ghcr.io serves Docker media types for images pushed as such regardless of what
# we ask for, so every type we can handle is advertised here.
_ACCEPT_MANIFEST = (
    f"{_MEDIA_TYPE_OCI_IMAGE_INDEX_V1}, {_MEDIA_TYPE_OCI_IMAGE_MANIFEST_V1}, "
    f"{_MEDIA_TYPE_MANIFEST_LIST_V2}, {_MEDIA_TYPE_MANIFEST_V2}"
)

_ModelT = TypeVar("_ModelT", bound=BaseModel)


def _validate(model: type[_ModelT], payload: object) -> _ModelT:
    """Validate a registry response against a model.

    Parameters
    ----------
    model : type[_ModelT]
        model to validate against
    payload : object
        decoded JSON response

    Returns:
    -------
    _ModelT
        validated model instance

    Raises:
    ------
    InvalidManifestError
        raise if the response does not match the model

    """
    try:
        return model.model_validate(payload)
    except ValidationError as err:
        msg = f"{model.__name__} does not match the registry response: {err}"
        raise InvalidManifestError(msg) from err


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

        Returns:
        -------
        str
            svg string of generated badge of package tags

        Raises:
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
            value=str(badge_value),
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

        Returns:
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
            value=str(badge_value),
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

        Returns:
        -------
        str
            svg string of generated badge of size

        """
        try:
            manifest = self.get_manifest(package_owner, package_name, tag=tag)
        except (InvalidManifestError, InvalidMediaTypeError):
            return self.get_invalid_badge(label)
        size = f"{manifest.total_size}B"
        badge = Badge(
            label=label,
            value=str(format_size(parse_size(size), binary=True)),
            default_color=self.color,
        )
        return str(badge.badge_svg_text)

    def get_manifest(
        self: Self,
        package_owner: str,
        package_name: str,
        *,
        tag: str = "latest",
        _depth: int = 0,
    ) -> ImageManifest:
        """Get manifest from ghcr api.

        An index (multi-arch image) is resolved to the manifest of one of the
        images it points at.

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
        _depth : int, optional
            current index resolution depth, used internally to stop cycles

        Returns:
        -------
        ImageManifest
            validated manifest of a single image

        Raises:
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

        if _depth > _MAX_INDEX_DEPTH:
            msg = f"Index resolution exceeded {_MAX_INDEX_DEPTH} levels."
            raise InvalidManifestError(msg)

        token = self.__auth(package_owner, package_name)
        url = f"https://ghcr.io/v2/{package_owner}/{package_name}/manifests/{tag}"
        manifest = requests.get(
            url,
            headers={
                "User-Agent": _USER_AGENT,
                "Authorization": f"Bearer {token}",
                "Accept": _ACCEPT_MANIFEST,
            },
            timeout=_TIMEOUT,
        ).json()

        if not isinstance(manifest, dict):
            msg = "manifest is empty."
            raise InvalidManifestError(msg)

        if "errors" in manifest:
            errors = ErrorResponse.model_validate(manifest).describe()
            msg = f"manifest contains some error: {errors}"
            raise InvalidManifestError(msg)

        media_type = manifest.get("mediaType")

        if media_type in (_MEDIA_TYPE_MANIFEST_V2, _MEDIA_TYPE_OCI_IMAGE_MANIFEST_V1):
            return _validate(ImageManifest, manifest)

        if media_type in (_MEDIA_TYPE_MANIFEST_LIST_V2, _MEDIA_TYPE_OCI_IMAGE_INDEX_V1):
            index = _validate(ImageIndex, manifest)
            descriptor = index.pick_image_descriptor()
            if descriptor is None:
                msg = "Returned list of manifest is empty."
                raise InvalidManifestError(msg)
            return self.get_manifest(
                package_owner,
                package_name,
                tag=descriptor.digest,
                _depth=_depth + 1,
            )

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

        Returns:
        -------
        list[str]
            tags, e.g. '1.0.0'

        Raises:
        ------
        InvalidTagListError
            raise if response is invalid

        """
        token = self.__auth(package_owner, package_name)
        url = f"https://ghcr.io/v2/{package_owner}/{package_name}/tags/list"
        params = {
            "n": 300,
        }
        payload = requests.get(
            url,
            headers={"User-Agent": _USER_AGENT, "Authorization": f"Bearer {token}"},
            timeout=10,
            params=params,
        ).json()

        try:
            tag_list = TagList.model_validate(payload)
        except ValidationError as err:
            raise InvalidTagListError from err

        if not tag_list.tags:
            raise InvalidTagListError
        return tag_list.tags

    def filter_tags(self: Self, package_owner: str, package_name: str) -> list[str]:
        """Filter tags by regex pattern.

        Parameters
        ----------
        package_owner : str
            package owner name
        package_name : str
            package name

        Returns:
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

        Returns:
        -------
        str
            svg string

        """
        badge = Badge(label=label, value=str("invalid"), default_color="#e05d44")
        return str(badge.badge_svg_text)

    @staticmethod
    def __auth(package_owner: str, package_name: str) -> str:
        m_user = re.match(_GITHUB_USER_PATTERN, package_owner)
        m_repo = re.match(_GITHUB_REPO_PATTERN, package_name)
        if m_user is None or m_repo is None:
            raise InvalidImageError
        token = base64.b64encode(f"v1:{package_owner}/{package_name}:0".encode())
        return token.decode("utf-8")
