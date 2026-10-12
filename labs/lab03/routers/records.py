"""Маршрути для роботи із записами."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException, Path, Query

from labs.lab03 import config, repository, schemas

router = APIRouter(prefix="/records", tags=["records"])

RecordId = Annotated[int, Path(gt=0, description="Ідентифікатор запису")]


def _map_conflict(error: sqlite3.IntegrityError) -> HTTPException:
    return HTTPException(
        status_code=409, detail="Порушено унікальність або обмеження даних"
    )


@router.get(
    "",
    response_model=list[schemas.RecordRead],
    summary="Список записів із фільтрами",
)
def list_records(
    category_id: Annotated[int | None, Query(gt=0)] = None,
    status: Annotated[schemas.Status | None, Query()] = None,
    min_value: Annotated[int | None, Query(ge=config.VALUE_MIN)] = None,
    q: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=config.MAX_LIMIT)] = (
        config.DEFAULT_LIMIT
    ),
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[dict]:
    """Повертає записи з фільтрами (AND) і пагінацією за id."""
    return repository.list_records(
        category_id=category_id,
        status=status,
        min_value=min_value,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=schemas.RecordRead,
    status_code=201,
    summary="Створити запис",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Дублікат code"},
    },
)
def create_record(payload: schemas.RecordCreate) -> dict:
    """Створює запис; неіснуюча категорія — 404, дублікат — 409."""
    try:
        return repository.create_record(payload.model_dump())
    except repository.CategoryNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Категорію не знайдено"
        ) from error
    except sqlite3.IntegrityError as error:
        raise _map_conflict(error) from error


@router.post(
    "/bulk",
    response_model=list[schemas.RecordRead],
    status_code=201,
    summary="Пакетне створення записів",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Дублікат code"},
    },
)
def bulk_create_records(
    payload: Annotated[
        list[schemas.RecordCreate],
        Body(
            min_length=config.BULK_MIN_ITEMS, max_length=config.BULK_MAX_ITEMS
        ),
    ],
) -> list[dict]:
    """Атомарно створює пакет записів (1–100) в одній транзакції."""
    try:
        return repository.bulk_create_records(
            [item.model_dump() for item in payload]
        )
    except repository.CategoryNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Категорію не знайдено"
        ) from error
    except sqlite3.IntegrityError as error:
        raise _map_conflict(error) from error


@router.get(
    "/{record_id}",
    response_model=schemas.RecordRead,
    summary="Отримати запис за id",
    responses={404: {"description": "Запис не знайдено"}},
)
def get_record(record_id: RecordId) -> dict:
    """Повертає один запис або 404."""
    record = repository.get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Запис не знайдено")
    return record


@router.put(
    "/{record_id}",
    response_model=schemas.RecordRead,
    summary="Повністю замінити змінювані поля запису",
    responses={
        404: {"description": "Запис або категорію не знайдено"},
        409: {"description": "Дублікат code"},
    },
)
def replace_record(
    record_id: RecordId, payload: schemas.RecordReplace
) -> dict:
    """Замінює всі змінювані поля запису; id не змінюється."""
    try:
        return repository.replace_record(record_id, payload.model_dump())
    except repository.RecordNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Запис не знайдено"
        ) from error
    except repository.CategoryNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Категорію не знайдено"
        ) from error
    except sqlite3.IntegrityError as error:
        raise _map_conflict(error) from error


@router.delete(
    "/{record_id}",
    status_code=204,
    summary="Видалити запис",
    responses={404: {"description": "Запис не знайдено"}},
)
def delete_record(record_id: RecordId) -> None:
    """Видаляє запис або повертає 404."""
    if not repository.delete_record(record_id):
        raise HTTPException(status_code=404, detail="Запис не знайдено")
