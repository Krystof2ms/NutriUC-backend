FROM ghcr.io/astral-sh/uv:python3.14-alpine AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    linux-headers

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-install-project

COPY . /app

RUN uv sync --locked


FROM python:3.14-alpine AS runtime

WORKDIR /app

RUN addgroup -S www-group && \
    adduser -S -G www-group -h /app www-app

COPY --from=builder --chown=www-app:www-group /app /app

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER www-app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
