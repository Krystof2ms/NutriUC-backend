FROM ghcr.io/astral-sh/uv:alpine3.23

WORKDIR /app

EXPOSE 8000

RUN apk add --no-cache \
    build-base \
    linux-headers

RUN addgroup -S www-group && \
    adduser -S -G www-group -h /app www-app

COPY pyproject.toml uv.lock ./

RUN uv sync --locked --no-dev --no-cache

RUN chown -R www-app:www-group /app

COPY --chown=www-app:www-group ./ ./

USER www-app

CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
