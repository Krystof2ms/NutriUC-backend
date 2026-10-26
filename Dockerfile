FROM ghcr.io/astral-sh/uv:alpine3.23

WORKDIR /app

EXPOSE 8000

COPY ./ ./
RUN uv sync --locked

COPY ./dist ./dist

CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
