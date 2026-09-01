FROM python:3.14-slim@sha256:656d12e70054d5fda18a045e2494c96701e9792dd1445f95b3d038df954f57e9 AS builder

ARG VERSION
ENV VERSION=${VERSION:-master}

RUN pip install --upgrade pip
RUN apt update && apt install -y git
RUN ln -s /usr/local/bin/python3 /usr/bin/python3
RUN /usr/bin/python3 -m venv /opt/venv
RUN /opt/venv/bin/pip install git+https://github.com/eggplants/ghcr-badge@${VERSION}

FROM al3xos/python-distroless:3.14.7-debian13@sha256:421a2331f5bf33de9ef3073759f3674ae6765f09e23bf83152998e870d44a836
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.14/site-packages"

ENTRYPOINT ["python", "/opt/venv/bin/ghcr-badge-server"]
