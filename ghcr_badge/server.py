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
                    "/<string:package_owner>/<string:package_name>/tags?color=...",
                    "/<string:package_owner>/<string:package_name>/latest_tag?color=...",
                    "/<string:package_owner>/<string:package_name>/size?tag=...&color=...",
                ],
                "example_paths": [
                    "/",
                    "/eggplants/ghcr-badge/tags",
                    "/eggplants/ghcr-badge/latest_tag",
                    "/eggplants/ghcr-badge/size?tag=latest",
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
        return return_svg(
            GHCRBadgeGenerator(color_type).generate_tags(package_owner, package_name)
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


@app.route("/<string:package_owner>/<string:package_name>/latest_tag", methods=["GET"])
def get_latest_tag(package_owner: str, package_name: str) -> Any:
    try:
        q_params = request.args
        color_type = q_params.get("color", "#44cc11")
        return return_svg(
            GHCRBadgeGenerator(color_type).generate_latest_tag(
                package_owner, package_name
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
        return return_svg(
            GHCRBadgeGenerator(color_type).generate_size(
                package_owner, package_name, tag_type
            )
        )
    except Exception as err:
        return jsonify(exception=type(err).__name__)


def main() -> None:
    app.run(host="0.0.0.0", port=int(environ.get("PORT", 5000)), debug=True)


if __name__ == "__main__":
    main()
