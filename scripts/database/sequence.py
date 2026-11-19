from typing import Any


async def sync_identity_sequence(
    connection: Any, table: str, column: str = "id"
) -> None:
    """Align an identity/serial sequence with the current maximum column value."""
    quoted_table = '"' + table.replace('"', '""') + '"'
    quoted_column = '"' + column.replace('"', '""') + '"'
    next_value = await connection.fetchval(
        f"SELECT COALESCE(MAX({quoted_column}), 0) + 1 FROM {quoted_table}"
    )
    await connection.execute(
        """
        SELECT setval(
            pg_get_serial_sequence($1, $2),
            $3,
            false
        )
        """,
        f'"{table}"',
        column,
        next_value,
    )
