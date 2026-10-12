"""Параметризовані SQL-запити до бази (шар доступу до даних)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import Any

from labs.lab03.database import get_connection


class CategoryNotFoundError(Exception):
    """Категорію з вказаним id не знайдено."""


class RecordNotFoundError(Exception):
    """Запис із вказаним id не знайдено."""


_SELECT_RECORD = """
    SELECT r.id, r.code, r.title, r.category_id, r.value, r.status,
           c.name AS category_name
    FROM records AS r
    JOIN categories AS c ON c.id = r.category_id
"""


def _category_exists(connection: sqlite3.Connection, category_id: int) -> bool:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return row is not None


def _fetch_record(
    connection: sqlite3.Connection, record_id: int
) -> dict[str, Any] | None:
    row = connection.execute(
        f"{_SELECT_RECORD} WHERE r.id = ?", (record_id,)
    ).fetchone()
    return dict(row) if row is not None else None


def list_categories() -> list[dict[str, Any]]:
    """Повертає всі категорії за зростанням id."""
    with closing(get_connection()) as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id ASC"
        ).fetchall()
        return [dict(row) for row in rows]


def create_category(name: str) -> dict[str, Any]:
    """Створює категорію та повертає її запис."""
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "INSERT INTO categories (name) VALUES (?)", (name,)
            )
            category_id = int(cursor.lastrowid)
        row = connection.execute(
            "SELECT id, name FROM categories WHERE id = ?", (category_id,)
        ).fetchone()
        return dict(row)


def delete_category(category_id: int) -> None:
    """Видаляє порожню категорію; за наявності записів — IntegrityError."""
    with closing(get_connection()) as connection:
        with connection:
            if not _category_exists(connection, category_id):
                raise CategoryNotFoundError(category_id)
            connection.execute(
                "DELETE FROM categories WHERE id = ?", (category_id,)
            )


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Додає новий запис і повертає його з назвою категорії."""
    with closing(get_connection()) as connection:
        with connection:
            if not _category_exists(connection, data["category_id"]):
                raise CategoryNotFoundError(data["category_id"])
            cursor = connection.execute(
                """
                INSERT INTO records
                    (code, title, category_id, value, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    data["code"],
                    data["title"],
                    data["category_id"],
                    data["value"],
                    data["status"],
                ),
            )
            record_id = int(cursor.lastrowid)
            result = _fetch_record(connection, record_id)
        return result


def get_record(record_id: int) -> dict[str, Any] | None:
    """Повертає запис за id або None."""
    with closing(get_connection()) as connection:
        return _fetch_record(connection, record_id)


def list_records(
    category_id: int | None = None,
    status: str | None = None,
    min_value: int | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Повертає записи з фільтрами та пагінацією, сортовані за id."""
    clauses: list[str] = []
    params: list[Any] = []
    if category_id is not None:
        clauses.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        clauses.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        clauses.append("r.value >= ?")
        params.append(min_value)
    if q is not None:
        clauses.append("instr(r.title, ?) > 0")
        params.append(q)

    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    query = f"{_SELECT_RECORD}{where} ORDER BY r.id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with closing(get_connection()) as connection:
        rows = connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def replace_record(
    record_id: int, data: dict[str, Any]
) -> dict[str, Any] | None:
    """Повністю замінює змінювані поля запису."""
    with closing(get_connection()) as connection:
        with connection:
            if _fetch_record(connection, record_id) is None:
                raise RecordNotFoundError(record_id)
            if not _category_exists(connection, data["category_id"]):
                raise CategoryNotFoundError(data["category_id"])
            connection.execute(
                """
                UPDATE records
                SET code = ?, title = ?, category_id = ?, value = ?,
                    status = ?
                WHERE id = ?
                """,
                (
                    data["code"],
                    data["title"],
                    data["category_id"],
                    data["value"],
                    data["status"],
                    record_id,
                ),
            )
            return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> bool:
    """Видаляє запис; повертає True, якщо запис існував."""
    with closing(get_connection()) as connection:
        with connection:
            cursor = connection.execute(
                "DELETE FROM records WHERE id = ?", (record_id,)
            )
            return cursor.rowcount > 0


def bulk_create_records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Атомарно додає пакет записів в одній транзакції."""
    with closing(get_connection()) as connection:
        with connection:
            for item in items:
                if not _category_exists(connection, item["category_id"]):
                    raise CategoryNotFoundError(item["category_id"])
            created: list[dict[str, Any]] = []
            for item in items:
                cursor = connection.execute(
                    """
                    INSERT INTO records
                        (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        item["code"],
                        item["title"],
                        item["category_id"],
                        item["value"],
                        item["status"],
                    ),
                )
                created.append(_fetch_record(connection, cursor.lastrowid))
            return created
