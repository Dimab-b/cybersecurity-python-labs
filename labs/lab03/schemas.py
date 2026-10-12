"""Pydantic-моделі запитів і відповідей (Pydantic 2)."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03 import config

Status = Literal["new", "in_progress", "done"]

BASE_CONFIG = ConfigDict(
    str_strip_whitespace=True,
    extra="forbid",
)


class CategoryCreate(BaseModel):
    """Модель створення категорії."""

    model_config = BASE_CONFIG

    name: str = Field(min_length=2, max_length=config.MAX_CATEGORY_NAME_LENGTH)


class CategoryRead(BaseModel):
    """Модель відповіді з категорією."""

    model_config = BASE_CONFIG

    id: int = Field(gt=0)
    name: str


class RecordCreate(BaseModel):
    """Модель створення запису (клієнт не задає id)."""

    model_config = BASE_CONFIG

    code: str = Field(min_length=3, max_length=config.MAX_CODE_LENGTH)
    title: str = Field(min_length=3, max_length=config.MAX_TITLE_LENGTH)
    category_id: int = Field(gt=0)
    value: int = Field(ge=config.VALUE_MIN)
    status: Status


class RecordReplace(RecordCreate):
    """Модель повної заміни запису (усі змінювані поля обов'язкові)."""


class RecordRead(RecordCreate):
    """Модель відповіді із записом та назвою категорії."""

    id: int = Field(gt=0)
    category_name: str
