FROM ghcr.io/astral-sh/uv:alpine3.23 AS builder

WORKDIR /app

RUN apk add --no-cache \
    build-base \
    linux-headers

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-cache

COPY ./ ./

RUN uv sync --locked --no-dev --no-cache


FROM python:3.13-alpine AS runtime

WORKDIR /app

RUN addgroup -S www-group && \
    adduser -S -G www-group -h /app www-app

COPY --from=builder --chown=www-app:www-group /app/.venv /app/.venv
COPY --from=builder --chown=www-app:www-group /app/src /app/src
COPY --from=builder --chown=www-app:www-group /app/dist /app/dist

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER www-app

EXPOSE 8000

CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
