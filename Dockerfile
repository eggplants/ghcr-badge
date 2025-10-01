FROM python:3.13.7-slim AS builder

ARG VERSION
ENV VERSION=${VERSION:-master}

RUN pip install --upgrade pip
RUN apt update && apt install -y git
RUN ln -s /usr/local/bin/python3 /usr/bin/python3
RUN /usr/bin/python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install git+https://github.com/eggplants/ghcr-badge@${VERSION}

FROM gcr.io/distroless/python3-debian12:nonroot
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

ENTRYPOINT ["ghcr-badge-server"]
