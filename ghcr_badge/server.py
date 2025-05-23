"""Serve Badge API Server."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from os import environ
from typing import TYPE_CHECKING

from flask import Flask, jsonify, make_response, render_template, request
from flask.wrappers import Response
from waitress import serve

from . import __version__
from .generate import GHCRBadgeGenerator

if TYPE_CHECKING:
    from typing import Literal


_PACKAGE_PARAM_RULE = "/<package_owner>/<path:package_name>"
_REPO_LINK = "https://github.com/eggplants/ghcr-badge"

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True


def return_svg(svg: str) -> Response:
    """Return a generated svg as `Flask.Response`.

    Parameters
    ----------
    svg : str
        svg source string

    Returns:
    -------
    Response
        Flask response object

    """
    expiry_time = datetime.now(tz=timezone.utc) + timedelta(3666)

    res = make_response(
        svg,
    )
    res.mimetype = "image/svg+xml"
    res.headers["Cache-Control"] = "max-age=3666,s-maxage=3666,no-store,proxy-revalidate"
    res.headers["Pragma"] = "no-cache"  # for HTTP 1.0
    res.headers["Expires"] = expiry_time.strftime("%a, %d %b %Y %H:%M:%S GMT")

    return res


@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
@app.route("/index<any('.html', '.json'):ext>", methods=["GET"])
def get_index(ext: Literal[".html", ".json"] = ".html") -> Response:
    """Handle GET `/`.

    Returns:
    -------
    Response
        JSON or HTML

    """
    if ext == ".json":
        return __get_index_json()
    return __get_index_html()


def __get_index_html() -> Response:
    """Handle GET `/` and response as html.

    Returns:
    -------
    Response
        HTML

    """
    return Response(render_template("index.j2", version=__version__, repo_link=_REPO_LINK))


def __get_index_json() -> Response:
    """Handle GET `/` and response as json.

    Returns:
    -------
    Response
        JSON

    """
    try:
        return jsonify(
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
                ],
                "repo": _REPO_LINK,
                "version": __version__,
            },
        )
    except Exception as err:  # noqa: BLE001
        return jsonify(exception=type(err).__name__)


@app.route(f"{_PACKAGE_PARAM_RULE}/tags", methods=["GET"])
def get_tags(package_owner: str, package_name: str) -> Response:
    """Get tags as a badge.

    Parameters
    ----------
    package_owner : str
        package owner name, e.g. 'eggplants'
    package_name : str
        package name, e.g. 'asciiquarium-docker'

    Returns:
    -------
    Response
        Tag badge

    """
    try:
        q_params = request.args
        color = q_params.get("color", "#44cc11")
        ignore_tag = q_params.get("ignore", "latest")
        label = q_params.get("label", "image tags")
        tag_num = q_params.get("n", 3)
        trim = q_params.get("trim", "")
        res = return_svg(
            GHCRBadgeGenerator(
                color=color,
                ignore_tag=ignore_tag,
                trim_type=trim,
            ).generate_tags(
                package_owner,
                package_name,
                n=int(tag_num),
                label=label,
            ),
        )
    except Exception as err:  # noqa: BLE001
        return jsonify(exception=type(err).__name__, message=str(err))

    return res


@app.route(f"{_PACKAGE_PARAM_RULE}/latest_tag", methods=["GET"])
def get_latest_tag(package_owner: str, package_name: str) -> Response:
    """Get a latest_tag as a badge.

    Parameters
    ----------
    package_owner : str
        package owner name, e.g. 'eggplants'
    package_name : str
        package name, e.g. 'asciiquarium-docker'

    Returns:
    -------
    Response
        latest tag badge

    """
    try:
        q_params = request.args
        color = q_params.get("color", "#44cc11")
        ignore_tag = q_params.get("ignore", "latest")
        label = q_params.get("label", "version")
        trim = q_params.get("trim", "")
        res = return_svg(
            GHCRBadgeGenerator(
                color=color,
                ignore_tag=ignore_tag,
                trim_type=trim,
            ).generate_latest_tag(
                package_owner,
                package_name,
                label=label,
            ),
        )
    except Exception as err:  # noqa: BLE001
        return jsonify(exception=type(err).__name__)

    return res


@app.route(f"{_PACKAGE_PARAM_RULE}/size", methods=["GET"])
def get_size(package_owner: str, package_name: str) -> Response:
    """Get image size as a badge.

    Parameters
    ----------
    package_owner : str
        package owner name, e.g. 'eggplants'
    package_name : str
        package name, e.g. 'asciiquarium-docker'

    Returns:
    -------
    Response
        image size badge

    """
    try:
        q_params = request.args
        tag = q_params.get("tag", "latest")
        color = q_params.get("color", "#44cc11")
        label = q_params.get("label", "image size")
        trim = q_params.get("trim", "")
        res = return_svg(
            GHCRBadgeGenerator(color=color, trim_type=trim).generate_size(
                package_owner,
                package_name,
                tag=tag,
                label=label,
            ),
        )
    except Exception as err:  # noqa: BLE001
        return jsonify(exception=type(err).__name__)

    return res


@app.route("/health")
def health() -> Response:
    """Check if server is up."""
    res = make_response("OK", 200)
    res.mimetype = "text/plain"
    return res


def main() -> None:
    """Run API server at `0.0.0.0:5000`."""
    host = environ.get("HOST", "0.0.0.0")  # noqa: S104
    port = int(environ.get("PORT", "5000"))
    serve(app, host=host, port=port)


if __name__ == "__main__":
    main()
