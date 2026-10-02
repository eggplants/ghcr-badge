FROM python:3.14-slim@sha256:0741d101873c12ab927e6f8653feb8862b9bd58771177acb1b885b95141f91b4 AS builder

ARG VERSION
ENV VERSION=${VERSION:-master}

RUN pip install --upgrade pip
RUN apt update && apt install -y git
RUN ln -s /usr/local/bin/python3 /usr/bin/python3
RUN /usr/bin/python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install git+https://github.com/eggplants/ghcr-badge@${VERSION}

FROM al3xos/python-distroless:3.14.7-debian13@sha256:ccb9409a6513569adfda0358cbd6d89ccda0933ba807b4f0eac09e0d7f2bf749
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.14/site-packages"

ENTRYPOINT ["python", "/opt/venv/bin/ghcr-badge-server"]
