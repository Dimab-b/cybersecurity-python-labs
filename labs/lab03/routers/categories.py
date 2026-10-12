"""Маршрути для роботи з категоріями."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path

from labs.lab03 import repository, schemas

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get(
    "",
    response_model=list[schemas.CategoryRead],
    summary="Список категорій",
)
def list_categories() -> list[dict]:
    """Повертає всі категорії за зростанням id."""
    return repository.list_categories()


@router.post(
    "",
    response_model=schemas.CategoryRead,
    status_code=201,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(payload: schemas.CategoryCreate) -> dict:
    """Створює категорію; дублікат назви — 409."""
    try:
        return repository.create_category(payload.name)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Категорія з такою назвою вже існує",
        ) from error


@router.delete(
    "/{category_id}",
    status_code=204,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def delete_category(
    category_id: Annotated[int, Path(gt=0, description="Ідентифікатор")],
) -> None:
    """Видаляє порожню категорію; непорожня — 409."""
    try:
        repository.delete_category(category_id)
    except repository.CategoryNotFoundError as error:
        raise HTTPException(
            status_code=404, detail="Категорію не знайдено"
        ) from error
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Категорія містить записи й не може бути видалена",
        ) from error
