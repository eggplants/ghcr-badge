"""Serve Badge API Server."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from os import environ
from pathlib import Path
from typing import Annotated, TypeVar

import uvicorn
from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from . import __version__
from .generate import GHCRBadgeGenerator

_PACKAGE_PARAM_RULE = "/{package_owner}/{package_name:path}"
_REPO_LINK = "https://github.com/eggplants/ghcr-badge"
_HERE = Path(__file__).parent

_RouteFunc = TypeVar("_RouteFunc", bound=Callable[..., Response])


class PrettyJSONResponse(JSONResponse):
    """JSON response indented for human readers."""

    def render(self: PrettyJSONResponse, content: object) -> bytes:
        """Serialize `content` as indented JSON.

        Parameters
        ----------
        content : object
            payload to serialize

        Returns:
        -------
        bytes
            encoded JSON body

        """
        return json.dumps(content, indent=2).encode()


class BadgeQuery(BaseModel):
    """Query parameters shared by every badge endpoint."""

    color: str = "#44cc11"
    trim: str = ""


class TagsQuery(BadgeQuery):
    """Query parameters of `/<owner>/<name>/tags`."""

    ignore: str = "latest"
    label: str = "image tags"
    n: int = 3


class LatestTagQuery(BadgeQuery):
    """Query parameters of `/<owner>/<name>/latest_tag`."""

    ignore: str = "latest"
    label: str = "version"


class SizeQuery(BadgeQuery):
    """Query parameters of `/<owner>/<name>/size`."""

    label: str = "image size"
    tag: str = "latest"


app = FastAPI(default_response_class=PrettyJSONResponse)
app.mount("/static", StaticFiles(directory=_HERE / "static"), name="static")
templates = Jinja2Templates(directory=_HERE / "templates")


def get_route(*paths: str) -> Callable[[_RouteFunc], _RouteFunc]:
    """Register a handler for GET and HEAD on each of `paths`.

    Badge consumers such as GitHub's Camo probe with HEAD, which Flask used to answer
    automatically. HEAD is hidden from the OpenAPI schema so that it does not collide
    with the operation id of its GET counterpart.

    Parameters
    ----------
    paths : str
        route paths to register

    Returns:
    -------
    Callable[[_RouteFunc], _RouteFunc]
        decorator registering the handler

    """

    def decorator(func: _RouteFunc) -> _RouteFunc:
        for path in paths:
            app.head(path, include_in_schema=False)(func)
            app.get(path)(func)
        return func

    return decorator


def return_svg(svg: str) -> Response:
    """Return a generated svg as a `Response`.

    Parameters
    ----------
    svg : str
        svg source string

    Returns:
    -------
    Response
        response object

    """
    expiry_time = datetime.now(tz=timezone.utc) + timedelta(3666)

    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={
            "Cache-Control": "max-age=3666,s-maxage=3666,no-store,proxy-revalidate",
            "Pragma": "no-cache",  # for HTTP 1.0
            "Expires": expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
        },
    )


@get_route("/", "/index", "/index.html")
def get_index(request: Request) -> Response:
    """Handle GET `/` and response as html.

    Parameters
    ----------
    request : Request
        incoming request, required by the template renderer

    Returns:
    -------
    Response
        HTML

    """
    return templates.TemplateResponse(
        request,
        "index.j2",
        {"version": __version__, "repo_link": _REPO_LINK},
    )


@get_route("/index.json")
def get_index_json() -> Response:
    """Handle GET `/index.json` and response as json.

    Returns:
    -------
    Response
        JSON

    """
    return PrettyJSONResponse(
        {
            "available_paths": [
                "/",
                "/<package_owner>/<package_name>/tags?color=...&ignore=...&n=...&label=...&trim=...",
                "/<package_owner>/<package_name>/latest_tag?color=...&ignore=...&label=...&trim=...",
                "/<package_owner>/<package_name>/size?tag=...&color=...&label=...&trim=...",
            ],
            "example_paths": [
                "/",
                "/eggplants/ghcr-badge/tags",
                "/eggplants/ghcr-badge/latest_tag",
                "/eggplants/ghcr-badge/size",
                "/frysztak/orpington-news/size",
                "/tuananh/aws-cli/size",
                "/plantuml/docker%2Fjekyll/tags",
                "/henrygd/beszel/beszel/tags",
            ],
            "repo": _REPO_LINK,
            "version": __version__,
        },
    )


@get_route("/health")
def health() -> Response:
    """Check if server is up.

    Returns:
    -------
    Response
        plain text `OK`

    """
    return PlainTextResponse("OK")


@get_route(f"{_PACKAGE_PARAM_RULE}/tags")
def get_tags(
    package_owner: str,
    package_name: str,
    query: Annotated[TagsQuery, Query()],
) -> Response:
    """Get tags as a badge.

    Parameters
    ----------
    package_owner : str
        package owner name, e.g. 'eggplants'
    package_name : str
        package name, e.g. 'asciiquarium-docker'
    query : TagsQuery
        query parameters

    Returns:
    -------
    Response
        Tag badge

    """
    try:
        res = return_svg(
            GHCRBadgeGenerator(
                color=query.color,
                ignore_tag=query.ignore,
                trim_type=query.trim,
            ).generate_tags(
                package_owner,
                package_name,
                n=query.n,
                label=query.label,
            ),
        )
    except Exception as err:  # noqa: BLE001
        return PrettyJSONResponse({"exception": type(err).__name__, "message": str(err)})

    return res


@get_route(f"{_PACKAGE_PARAM_RULE}/latest_tag")
def get_latest_tag(
    package_owner: str,
    package_name: str,
    query: Annotated[LatestTagQuery, Query()],
) -> Response:
    """Get a latest_tag as a badge.

    Parameters
    ----------
    package_owner : str
        package owner name, e.g. 'eggplants'
    package_name : str
        package name, e.g. 'asciiquarium-docker'
    query : LatestTagQuery
        query parameters

    Returns:
    -------
    Response
        latest tag badge

    """
    try:
        res = return_svg(
            GHCRBadgeGenerator(
                color=query.color,
                ignore_tag=query.ignore,
                trim_type=query.trim,
            ).generate_latest_tag(
                package_owner,
                package_name,
                label=query.label,
            ),
        )
    except Exception as err:  # noqa: BLE001
        return PrettyJSONResponse({"exception": type(err).__name__})

    return res


@get_route(f"{_PACKAGE_PARAM_RULE}/size")
def get_size(
    package_owner: str,
    package_name: str,
    query: Annotated[SizeQuery, Query()],
) -> Response:
    """Get image size as a badge.

    Parameters
    ----------
    package_owner : str
        package owner name, e.g. 'eggplants'
    package_name : str
        package name, e.g. 'asciiquarium-docker'
    query : SizeQuery
        query parameters

    Returns:
    -------
    Response
        image size badge

    """
    try:
        res = return_svg(
            GHCRBadgeGenerator(color=query.color, trim_type=query.trim).generate_size(
                package_owner,
                package_name,
                tag=query.tag,
                label=query.label,
            ),
        )
    except Exception as err:  # noqa: BLE001
        return PrettyJSONResponse({"exception": type(err).__name__})

    return res


def main() -> None:
    """Run API server at `0.0.0.0:5000`."""
    host = environ.get("HOST", "0.0.0.0")  # noqa: S104
    port = int(environ.get("PORT", "5000"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
