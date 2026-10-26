import asyncio
import json
import os
from pathlib import Path
from typing import Any

import asyncpg  # pyright: ignore[reportMissingTypeStubs]

DATABASE_DIR = Path(__file__).parent.parent / "database"


async def read_json(filename: str) -> list[dict[str, Any]]:  # pyright: ignore[reportExplicitAny]
    path = DATABASE_DIR / filename

    with path.open("r", encoding="utf-8") as file:
        data: list[dict[str, Any]] = json.load(file)  # pyright: ignore[reportAny, reportExplicitAny]
        return data


async def seed():
    conn = await asyncpg.connect(os.environ["DATABASE_URL"])

    try:
        users = await read_json("users.json")
        categories = await read_json("categories.json")
        recipes = await read_json("recipes.json")
        tips = await read_json("tips.json")
        roles = await read_json("roles.json")

        async with conn.transaction():
            await conn.execute('DELETE FROM "Recipe"')
            await conn.execute('DELETE FROM "Session"')
            await conn.execute('DELETE FROM "Tip"')
            await conn.execute('DELETE FROM "Category"')
            await conn.execute('DELETE FROM "User"')
            await conn.execute('DELETE FROM "Role"')

            # Category
            await conn.executemany(
                """
                INSERT INTO "Category"
                    ("id", "name", "description", "type")
                OVERRIDING SYSTEM VALUE
                VALUES ($1, $2, $3, $4)
                """,
                [
                    (
                        category["id"],
                        category["name"],
                        category["description"],
                        category["type"],
                    )
                    for category in categories
                ],
            )

            # Role
            await conn.executemany(
                """
                INSERT INTO "Role"
                    ("id", "name")
                OVERRIDING SYSTEM VALUE
                VALUES ($1, $2)
                """,
                [
                    (
                        role["id"],
                        role["name"],
                    )
                    for role in roles
                ],
            )

            # User
            await conn.executemany(
                """
                INSERT INTO "User"
                    (
                        "id",
                        "name",
                        "email",
                        "avatar_key",
                        "password_hash",
                        "status",
                        "role_id"
                    )
                OVERRIDING SYSTEM VALUE
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                [
                    (
                        user["id"],
                        user["name"],
                        user["email"],
                        user.get("avatar_key"),
                        user.get("password_hash"),
                        user.get("status", "active"),
                        user["role_id"],
                    )
                    for user in users
                ],
            )

            # Recipe
            await conn.executemany(
                """
                INSERT INTO "Recipe"
                    (
                        "name",
                        "origin",
                        "instructions",
                        "image_key",
                        "description",
                        "ingredients",
                        "category_id",
                        "user_id"
                    )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                [
                    (
                        recipe["name"],
                        recipe["origin"],
                        json.dumps(recipe["instructions"]),
                        recipe.get("image_key")
                        if recipe.get("image_key") is not None
                        else None,
                        recipe["description"],
                        json.dumps(recipe["ingredients"]),
                        recipe["category_id"],
                        recipe["user_id"],
                    )
                    for recipe in recipes
                ],
            )

            # Tip
            await conn.executemany(
                """
                INSERT INTO "Tip"
                    (
                        "title",
                        "content",
                        "category_id",
                        "user_id"
                    )
                VALUES ($1, $2, $3, $4)
                """,
                [
                    (
                        tip["title"],
                        tip["content"],
                        tip["category_id"],
                        tip["user_id"],
                    )
                    for tip in tips
                ],
            )

        print("Seed completado")

    except Exception as error:
        print(error)
        raise

    finally:
        await conn.close()


if __name__ == "__main__":
    print("seed")
    asyncio.run(seed())
