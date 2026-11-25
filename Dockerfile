FROM python:3.14-slim@sha256:930e1abba7c4e8f96ed93e8012c35d174d7732752731bbd5e8e757d7ec6f3966 AS builder

ARG VERSION
ENV VERSION=${VERSION:-master}

RUN pip install --upgrade pip
RUN apt update && apt install -y git
RUN ln -s /usr/local/bin/python3 /usr/bin/python3
RUN /usr/bin/python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install git+https://github.com/eggplants/ghcr-badge@${VERSION}

FROM al3xos/python-distroless:3.14.10-debian13@sha256:6e4b946fb54414a8f5eda4587f33de341f0d57c72327fccac88ae7234b56790c
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.14/site-packages"
# Numeric so that it works whether or not the base image defines a nonroot user.
USER 65532:65532

ENTRYPOINT ["python", "/opt/venv/bin/ghcr-badge-server"]
