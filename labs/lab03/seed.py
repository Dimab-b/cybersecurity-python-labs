"""Початкове заповнення бази даними з data/seed.json."""

from __future__ import annotations

import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from labs.lab03 import config
from labs.lab03.database import get_connection, initialize_database
from labs.lab03.schemas import RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


class CategorySeed(BaseModel):
    """Категорія з явним id для початкового набору."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=config.MAX_CATEGORY_NAME_LENGTH)


class SeedData(BaseModel):
    """Структура файлу seed.json."""

    model_config = ConfigDict(extra="forbid")

    categories: list[CategorySeed] = Field(min_length=1)
    records: list[RecordCreate] = Field(min_length=1)


class SeedError(Exception):
    """Помилка початкових даних або заповнення бази."""


def load_seed(path: Path = SEED_PATH) -> SeedData:
    """Читає та перевіряє файл початкових даних."""
    if not path.is_file():
        raise SeedError(f"Файл початкових даних не знайдено: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise SeedError(f"Некоректний JSON: {error}") from error
    try:
        return SeedData.model_validate(raw)
    except ValidationError as error:
        raise SeedError(f"Дані не пройшли перевірку: {error}") from error


def _is_empty(connection: sqlite3.Connection) -> bool:
    categories = connection.execute(
        "SELECT COUNT(*) FROM categories"
    ).fetchone()[0]
    records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories == 0 and records == 0


def seed_database(path: Path = SEED_PATH) -> bool:
    """Заповнює порожню базу в одній транзакції; вдруге нічого не змінює."""
    data = load_seed(path)
    with closing(get_connection()) as connection:
        if not _is_empty(connection):
            print("База вже містить дані — заповнення скасовано.")
            return False
        try:
            with connection:
                connection.executemany(
                    "INSERT INTO categories (id, name) VALUES (?, ?)",
                    [(item.id, item.name) for item in data.categories],
                )
                connection.executemany(
                    """
                    INSERT INTO records
                        (code, title, category_id, value, status)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            record.code,
                            record.title,
                            record.category_id,
                            record.value,
                            record.status,
                        )
                        for record in data.records
                    ],
                )
        except sqlite3.IntegrityError as error:
            raise SeedError(
                f"Порушення обмежень під час заповнення: {error}"
            ) from error

    print(
        f"Додано {len(data.categories)} категорій "
        f"і {len(data.records)} записів."
    )
    return True


def main() -> int:
    """Ініціалізує базу та виконує початкове заповнення."""
    try:
        initialize_database()
        seed_database()
    except SeedError as error:
        print(f"Помилка: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
