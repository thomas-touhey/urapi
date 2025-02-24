FROM alpine:3.19 AS builder

WORKDIR /opt/urapi

RUN \
    apk add --no-cache python3=3.11.11-r0 py3-pip=23.3.1-r0 \
    && python -m venv /opt/venv \
    && /opt/venv/bin/pip3 --no-cache-dir install poetry==1.8.5

COPY ./pyproject.toml .
COPY ./poetry.lock .

RUN \
    /opt/venv/bin/poetry export --only main,deployment \
        --format requirements.txt --with-credentials \
        --output requirements.txt \
    && python -m venv /opt/urapi/venv \
    && /opt/urapi/venv/bin/python -m pip install -r requirements.txt

FROM alpine:3.19 AS runtime
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

WORKDIR /opt/urapi
RUN apk add --no-cache python3=3.11.11-r0

COPY --from=builder /opt/urapi/venv /opt/urapi/venv

FROM runtime AS asgi
EXPOSE 80
WORKDIR /opt/urapi/root
ENTRYPOINT ["/opt/urapi/venv/bin/python", "-m", "uvicorn", "urapi.asgi:app", "--host", "0.0.0.0", "--port", "80", "--log-config", "/opt/urapi/root/docker/logging.dev.ini", "--reload"]

FROM runtime AS init-dev
WORKDIR /opt/urapi/root
ENV PYTHONPATH=/opt/urapi/root
ENTRYPOINT ["/opt/urapi/venv/bin/python", "/opt/urapi/root/docker/init_dev.py"]
