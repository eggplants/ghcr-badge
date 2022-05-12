FROM python:3

RUN pip install --upgrade pip

RUN python -m pip install git+https://github.com/eggplants/ghcr-badge

ENTRYPOINT ["ghcr-badge-server"]
