from os import environ
from typing import Any

from flask import Flask, jsonify, make_response, request
from flask.wrappers import Response

from .generate import GHCRBadgeGenerator

app = Flask(__name__)
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True


def return_svg(svg: str) -> Response:
    res = make_response(
        svg,
    )
    res.mimetype = "image/svg+xml"
    res.headers["Cache-Control"] = "max-age=3600, s-maxage=3600"
    # res.headers["Cache-Control"] = "nocache"
    return res


@app.route("/", methods=["GET"])
def get_index() -> Any:
    try:
        return jsonify(
            {
                "available_paths": [
                    "/",
                    "/<string:package_owner>/<string:package_name>/tags?color=...&ignore=...&n=...&label=...&trim=...",
                    "/<string:package_owner>/<string:package_name>/latest_tag?color=...&ignore=...&label=...&trim=...",
                    "/<string:package_owner>/<string:package_name>/develop_tag?color=...&label=...",
                    "/<string:package_owner>/<string:package_name>/size?tag=...&color=...&label=...&trim=...",
                ],
                "example_paths": [
                    "/",
                    "/eggplants/ghcr-badge/tags",
                    "/eggplants/ghcr-badge/latest_tag",
                    "/ptr727/plexcleaner/develop_tag",
                    "/eggplants/ghcr-badge/size",
                    "/frysztak/orpington-news/size",
                ],
                "repo": "https://github.com/eggplants/ghcr-badge",
            }
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


@app.route("/<string:package_owner>/<string:package_name>/tags", methods=["GET"])
def get_tags(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        color = q_params.get("color", "#44cc11")
        ignore_tag = q_params.get("ignore", "latest")
        label = q_params.get("label", "image tags")
        tag_num = q_params.get("n", 3)
        trim = q_params.get("trim", "")
        return return_svg(
            GHCRBadgeGenerator(
                color=color, ignore_tag=ignore_tag, trim_type=trim
            ).generate_tags(package_owner, package_name, n=int(tag_num), label=label)
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__, message=str(err))


@app.route("/<string:package_owner>/<string:package_name>/latest_tag", methods=["GET"])
def get_latest_tag(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        color = q_params.get("color", "#44cc11")
        ignore_tag = q_params.get("ignore", "latest")
        label = q_params.get("label", "version")
        trim = q_params.get("trim", "")
        return return_svg(
            GHCRBadgeGenerator(
                color=color, ignore_tag=ignore_tag, trim_type=trim
            ).generate_latest_tag(package_owner, package_name, label=label)
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


@app.route("/<string:package_owner>/<string:package_name>/develop_tag", methods=["GET"])
def get_develop_tag(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        color = q_params.get("color", "#44cc11")
        label = q_params.get("label", "develop")
        return return_svg(
            GHCRBadgeGenerator(color=color).generate_develop_tag(
                package_owner, package_name, label=label
            )
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


@app.route("/<string:package_owner>/<string:package_name>/size", methods=["GET"])
def get_size(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        tag = q_params.get("tag", "latest")
        color = q_params.get("color", "#44cc11")
        label = q_params.get("label", "image size")
        trim = q_params.get("trim", "")
        return return_svg(
            GHCRBadgeGenerator(color=color, trim_type=trim).generate_size(
                package_owner, package_name, tag=tag, label=label
            )
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


def main() -> None:
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))


if __name__ == "__main__":
    main()
