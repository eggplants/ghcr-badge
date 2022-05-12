from flask import Flask, request
from flask.wrappers import Response

from .generate import GHCRBadgeGenerator

app = Flask(__name__)


def return_svg(svg: str) -> Response:
    return Response(svg, mimetype="image/svg+xml")


@app.route("/<str:package_owner>/<str:package_name>/tags", methods=["GET"])
def get_tags(package_owner: str, package_name: str) -> Response:
    q_params = request.args
    color_type = q_params.get("color", "lime")
    return return_svg(
        GHCRBadgeGenerator(color_type).generate_tags(package_owner, package_name)
    )


@app.route("/<str:package_owner>/<str:package_name>/latest_tag", methods=["GET"])
def get_latest_tag(package_owner: str, package_name: str) -> Response:
    q_params = request.args
    color_type = q_params.get("color", "lime")
    return return_svg(
        GHCRBadgeGenerator(color_type).generate_latest_tag(package_owner, package_name)
    )


@app.route("/<str:package_owner>/<str:package_name>/size", methods=["GET"])
def get_size(package_owner: str, package_name: str) -> Response:
    q_params = request.args
    tag_type = q_params.get("tag", "latest")
    color_type = q_params.get("color", "lime")
    return return_svg(
        GHCRBadgeGenerator(color_type).generate_size(
            package_owner, package_name, tag_type
        )
    )


def main() -> None:
    app.run(debug=True)


if __name__ == "__main__":
    main()
