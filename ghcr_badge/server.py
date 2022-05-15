from os import environ
from typing import Any

from flask import Flask, jsonify, request
from flask.wrappers import Response

from .generate import GHCRBadgeGenerator

app = Flask(__name__)


def return_svg(svg: str) -> Response:
    return Response(svg, mimetype="image/svg+xml")


@app.route("/", methods=["GET"])
def get_index() -> Any:
    try:
        return jsonify(
            {
                "available_paths": [
                    "/",
                    "/<string:package_owner>/<string:package_name>/tags?color=...&ignore=...&n=...&label=...",
                    "/<string:package_owner>/<string:package_name>/latest_tag?color=...&ignore=...&label=...",
                    "/<string:package_owner>/<string:package_name>/develop_tag?color=...&label=...",
                    "/<string:package_owner>/<string:package_name>/size?tag=...&color=...&label=...",
                ],
                "example_paths": [
                    "/",
                    "/eggplants/ghcr-badge/tags",
                    "/eggplants/ghcr-badge/latest_tag",
                    "/ptr727/plexcleaner/develop_tag",
                    "/eggplants/ghcr-badge/size",
                ],
            }
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


@app.route("/<string:package_owner>/<string:package_name>/tags", methods=["GET"])
def get_tags(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        color_type = q_params.get("color", "#44cc11")
        ignore_tag = q_params.get("ignore", "latest")
        label = q_params.get("label", "image tags")

        tag_num = q_params.get("n", 3)
        return return_svg(
            GHCRBadgeGenerator(color=color_type, ignore_tag=ignore_tag).generate_tags(
                package_owner, package_name, n=int(tag_num), label=label
            )
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__, message=str(err))


@app.route("/<string:package_owner>/<string:package_name>/latest_tag", methods=["GET"])
def get_latest_tag(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        color_type = q_params.get("color", "#44cc11")
        ignore_tag = q_params.get("ignore", "latest")
        label = q_params.get("label", "version")
        return return_svg(
            GHCRBadgeGenerator(
                color=color_type, ignore_tag=ignore_tag
            ).generate_latest_tag(package_owner, package_name, label=label)
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


@app.route("/<string:package_owner>/<string:package_name>/develop_tag", methods=["GET"])
def get_develop_tag(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        color_type = q_params.get("color", "#44cc11")
        label = q_params.get("label", "develop")
        return return_svg(
            GHCRBadgeGenerator(color=color_type).generate_develop_tag(
                package_owner, package_name, label=label
            )
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


@app.route("/<string:package_owner>/<string:package_name>/size", methods=["GET"])
def get_size(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        tag_type = q_params.get("tag", "latest")
        color_type = q_params.get("color", "#44cc11")
        label = q_params.get("label", "image size")
        return return_svg(
            GHCRBadgeGenerator(color=color_type).generate_size(
                package_owner, package_name, tag_type, label=label
            )
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


def main() -> None:
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)))


if __name__ == "__main__":
    main()
