# NutriUC Backend

> Asynchronous RESTful and Real-Time API for nutrition, healthy recipes, dietary tips, and user management for **Web Saludable UC** (Universidad Continental).

[![Python Version](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-336791.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Architecture Docs](https://img.shields.io/badge/docs-Architecture-brightgreen.svg)](docs/architecture.md)

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
  - [1. Clone and Install Dependencies](#1-clone-and-install-dependencies)
  - [2. Configure Environment Variables](#2-configure-environment-variables)
  - [3. Start Database and Seed Data](#3-start-database-and-seed-data)
  - [4. Run Development Server](#4-run-development-server)
- [Environment Variables](#environment-variables)
- [Available Poe Tasks](#available-poe-tasks)
- [API Endpoints Overview](#api-endpoints-overview)
- [Real-Time Events (SSE) & Background Workers](#real-time-events-sse--background-workers)
- [Docker & Containerized Deployment](#docker--containerized-deployment)
- [Code Quality & Linting](#code-quality--linting)
- [License](#license)

---

## Overview

**NutriUC Backend** is a high-performance backend application engineered with **FastAPI** and **Python 3.14+**. It provides full-featured content management for healthy recipes and nutritional tips, user profile management with asynchronous image processing, and a robust dual-token authentication system using secure cookies.

Instead of heavy Object-Relational Mappers (ORMs), the backend utilizes native asynchronous PostgreSQL drivers (`asyncpg`) with raw parameterized SQL queries, guaranteeing high throughput, deterministic execution, and sub-millisecond database communication.

---

## Key Features

- **Asynchronous Architecture:** Non-blocking async endpoints throughout the entire request lifecycle.
- **Zero-ORM Direct SQL:** High-performance direct queries with `asyncpg` connection pooling and native PostgreSQL JSON/JSONB serialization.
- **Dual-Token Authentication (JWT + Sessions):**
  - Short-lived Access Token in `HttpOnly`, `SameSite=Lax` cookies.
  - Long-lived Refresh Token stored securely in `HttpOnly`, `SameSite=Strict` cookies.
  - Revocable database-backed sessions storing SHA-256 token hashes and unique JTIs.
  - Password hashing powered by **Argon2id** (`pwdlib`).
- **Keyset / Cursor-Based Pagination:** Efficient $O(\log N)$ bidirectional pagination for large recipe and tip catalogs without `OFFSET` bottlenecks.
- **Non-Blocking Background Workers:** In-memory job queues (`asyncio.Queue`) for CPU-heavy image cropping, Lanczos resampling, and WebP format conversion using **Pillow**.
- **Real-Time Push Notifications (SSE):** Server-Sent Events (`sse-starlette`) stream background media processing updates (`user.image_changed`, `recipe.image_changed`) directly to clients.
- **In-Memory Registry Caching:** Application-level caching for roles and categories initialized during lifespan startup.
- **Configurable Multi-Layer Tracing:** Granular tracing across API, Service, Repository, Database SQL, Worker, and Event layers via custom `@trace` decorators.

---

## Tech Stack

| Component | Technology | Description |
|---|---|---|
| **Language** | Python 3.14+ | Modern async Python with static type annotations |
| **Framework** | FastAPI 0.141+ | High-performance async web framework |
| **Package Manager** | [uv](https://github.com/astral-sh/uv) | Ultra-fast Python package installer and resolver |
| **Task Runner** | [Poe the Poet](https://github.com/nat-n/poethepoet) | Multi-task orchestration integrated with `pyproject.toml` |
| **Database** | PostgreSQL 18 | Relational database with UUIDv7, identity columns, and JSONB |
| **DB Driver** | `asyncpg` | Native, blazing-fast async PostgreSQL driver |
| **Security & Auth** | `pwdlib[argon2]`, `PyJWT` | Modern password hashing and JSON Web Tokens |
| **Media Processing** | Pillow (PIL) | EXIF correction, cropping, and WebP encoding |
| **Real-Time Streaming** | `sse-starlette` | Asynchronous Server-Sent Events implementation |
| **Linter & Type Checker** | `ruff`, `pyright` | Strict linting, formatting, and static type analysis |

---

## Architecture

For an in-depth breakdown of the design patterns, data flows, database schema, and sequence diagrams, refer to:

👉 **[Architecture Documentation (`docs/architecture.md`)](docs/architecture.md)**

```
┌──────────────┐       ┌────────────────┐       ┌────────────────────┐
│   Web / UI   │ <===> │ FastAPI (API)  │ <===> │ Services (Domain)  │
│    Client    │       └────────────────┘       └──────────┬─────────┘
└──────▲───────┘                │                          │
       │                        ▼                          ▼
       │ SSE             ┌─────────────┐       ┌──────────────────────┐
       └──────────────── │ Event / SSE │ <==== │ Repositories / asyncpg│
                         └──────▲──────┘       └──────────┬───────────┘
                                │                          │
                         ┌──────┴──────┐                   ▼
                         │ Async Queue │       ┌──────────────────────┐
                         │ & Workers   │       │    PostgreSQL 18     │
                         └─────────────┘       └──────────────────────┘
```

---

## Project Structure

```text
backend/
├── compose.prod.yaml          # Production Docker Compose definition
├── compose.yaml               # Development Docker Compose definition
├── database/
│   └── init.sql               # Database schema definition (PostgreSQL 18)
├── Dockerfile                 # Production multi-stage Docker image
├── Dockerfile.dev             # Development Docker image with hot-reload
├── docs/
│   └── architecture.md        # Comprehensive architecture documentation
├── pyproject.toml             # uv dependencies and Poe tasks configuration
├── README.md                  # Project documentation (this file)
├── resources.temp/            # Default local media directory (avatars, recipes)
├── scripts/
│   └── database/
│       ├── categories.json    # Seed data: Categories
│       ├── recipes.json       # Seed data: Recipes
│       ├── roles.json         # Seed data: Roles
│       ├── seed.py            # Database seeding script
│       ├── tips.json          # Seed data: Nutrition tips
│       └── users.json         # Seed data: Users
├── src/
│   └── app/
│       ├── api/               # API routes, dependencies, schemas, responses
│       ├── constants/         # Media limits and directory paths
│       ├── context_manager.py # Lifespan context (DB pool, workers, registries)
│       ├── core/              # Config, cookies, logger, queues, workers, tracing
│       ├── events/            # SSE Event definitions
│       ├── jobs/              # Background job definitions
│       ├── main.py            # FastAPI entrypoint and middleware setup
│       ├── models/            # Domain models and database representations
│       ├── repositories/      # asyncpg SQL query functions
│       └── services/          # Business logic and domain rules
└── uv.lock                    # Locked dependency versions
```

---

## Prerequisites

Ensure the following tools are installed on your workstation:

- **[Python](https://www.python.org/)**: Version `>= 3.14` (or `>= 3.12` when running through Docker)
- **[uv](https://docs.astral.sh/uv/)**: Recommended package and environment manager
- **[Docker & Docker Compose](https://www.docker.com/)**: For running the PostgreSQL 18 container and local services

---

## Getting Started

### 1. Clone and Install Dependencies

Using `uv`, synchronize virtual environment and lockfile:

```bash
# From the backend directory
uv sync
```

### 2. Configure Environment Variables

Copy the example environment configuration:

```bash
cp .env.example .env
```

Review and adjust variables according to your local environment (see [Environment Variables](#environment-variables)).

### 3. Start Database and Seed Data

Launch the PostgreSQL 18 container using Docker Compose:

```bash
docker compose up -d db
```

Run the database seed script to populate roles, categories, users, recipes, and tips:

```bash
uv run poe seed
```

### 4. Run Development Server

Start the FastAPI application with auto-reload:

```bash
uv run poe app --mode dev
```

The API will be available at:
- **Base API URL:** `http://localhost:3000/api/v1` (or port configured in `.env`)
- **Interactive OpenAPI Docs (Swagger UI):** `http://localhost:3000/docs`
- **ReDoc Documentation:** `http://localhost:3000/redoc`

---

## Environment Variables

| Variable | Type | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | String (PostgresDsn) | *Required* | PostgreSQL connection URI (`postgresql://user:pass@host:5432/dbname`) |
| `JWT_SECRET` | String | *Required* | Secret key for signing and validating JWT tokens |
| `FASTAPI_ENV` | String | `development` | Runtime environment: `development` or `production` |
| `CORS_ORIGINS` | JSON Array (List[str]) | `["*"]` in dev | Allowed CORS origins (e.g., `["http://localhost:5173"]`). Wildcard `*` rejected in production |
| `TRACE_LAYERS` | JSON Array (List[str]) | `[]` | Active tracing layers: `"api"`, `"service"`, `"repo"`, `"db"`, `"worker"`, `"events"` |
| `API_V1_STR` | String | `/api/v1` | URL prefix for version 1 API endpoints |
| `RESOURCES_DIR` | Path | `./resources.temp` | Directory path for saving processed media files (avatars, recipes) |
| `FRONTEND_DIR` | Path (Optional) | `./dist/frontend` | Directory of compiled static frontend assets to serve (if enabled) |

---

## Available Poe Tasks

Tasks are managed via [Poe the Poet](https://github.com/nat-n/poethepoet) defined in `pyproject.toml`:

```bash
# Run server in development mode (hot-reload enabled)
uv run poe app --mode dev

# Run server in production mode
uv run poe app --mode run

# Run server with a custom env file (e.g., .env.prod)
uv run poe app --mode run --env_file .env.prod

# Seed database with initial datasets
uv run poe seed --env_file .env

# Verify bytecode compilation across all src/ files
uv run poe compile
```

---

## API Endpoints Overview

All endpoints are versioned under `/api/v1` (configurable via `API_V1_STR`):

### 🔐 Authentication (`/auth`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/auth/login` | Authenticate user, set `access_token` and `refresh_token` cookies | No |
| `POST` | `/auth/refresh` | Validate refresh session and rotate access token | Via Refresh Cookie |
| `POST` | `/auth/logout` | Revoke active session in DB and clear auth cookies | Yes |

### 👤 User Management (`/users`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/users/` | Register a new user | No |
| `GET` | `/users/me` | Retrieve profile information of authenticated user | Yes |
| `GET` | `/users/me/stats` | Retrieve user activity statistics (recipes, tips counts) | Yes |
| `PATCH` | `/users/me` | Update authenticated user profile | Yes |
| `PUT` | `/users/me/avatar` | Upload and crop user avatar (asynchronously processed) | Yes |
| `DELETE` | `/users/me/avatar` | Delete user avatar | Yes |
| `GET` | `/users/{id}/avatar` | Serve avatar image by user public ID | No |

### 🥗 Recipes (`/recipes`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/recipes/search` | Search recipes with keyset pagination, category, and text filter | Optional |
| `GET` | `/recipes/{id}` | Get full recipe details by ID | Optional |
| `POST` | `/recipes/` | Create a new recipe | Yes |
| `PATCH` | `/recipes/{id}` | Update recipe details (author only) | Yes |
| `DELETE` | `/recipes/{id}` | Delete recipe (author only) | Yes |
| `PUT` | `/recipes/{id}/img` | Upload recipe cover image (asynchronously processed) | Yes |
| `GET` | `/recipes/recipe/{id}/img`| Serve recipe image file | No |
| `DELETE` | `/recipes/recipe/{id}/img`| Remove recipe cover image | Yes |

### 💡 Healthy Tips (`/tips`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/tips/search` | Search tips with keyset pagination and category filters | Optional |
| `GET` | `/tips/{id}` | Retrieve tip by ID | Optional |
| `POST` | `/tips/` | Publish a new nutrition tip | Yes |
| `PATCH` | `/tips/{id}` | Edit an existing tip (author only) | Yes |
| `DELETE` | `/tips/{id}` | Remove tip (author only) | Yes |

### 🏷️ Categories & System (`/categories`, `/events`, `/ping`)
| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/categories/names` | List registered recipe and tip categories | No |
| `GET` | `/events/events` | Real-time Server-Sent Events (SSE) notification stream | Yes |
| `GET` | `/ping` | Basic system health check | No |

---

## Real-Time Events (SSE) & Background Workers

1. When a client uploads an image (avatar or recipe photo), the endpoint immediately validates headers and saves a raw temporary file, enqueuing a job into `AvatarJobQueue` or `RecipeJobQueue`.
2. The HTTP endpoint returns an immediate `200 OK` response without waiting for CPU-intensive transformation.
3. The background worker picks up the job:
   - Normalizes orientation from EXIF tags.
   - Crops and resizes to standard resolutions using high-quality Lanczos interpolation.
   - Encodes image into modern **WebP** format.
   - Saves file to storage and updates database record.
4. The worker dispatches a typed event (`UserAvatarChanged` or `RecipeImageChanged`) through `event_manager`.
5. Connected clients listening on `GET /api/v1/events/events` receive real-time push updates over SSE:

```json
event: user.image_changed
data: {"message": "avatar accept"}
```

---

## Docker & Containerized Deployment

### Development Container

Run backend and PostgreSQL database with live reloading:

```bash
docker compose -f compose.yaml up --build
```

### Production Container

Run the multi-stage optimized production build:

```bash
docker compose -f compose.prod.yaml up -d --build
```

The production `Dockerfile` leverages `ghcr.io/astral-sh/uv:alpine3.23` for minimal image footprint and fast startup times.

---

## Code Quality & Linting

Ensure code conforms to formatting and typing guidelines:

```bash
# Run Ruff linter and formatter checks
uv run ruff check .
uv run ruff format --check .

# Run static type analysis using Pyright
uv run pyright

# Verify Python byte-compilation
uv run poe compile
```

---

## License

This project is licensed under the Apache-2.0 License. Refer to the root `LICENSE` file for details.
