"""FastAPI-застосунок лабораторної роботи №3."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from labs.lab03 import config
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Створює відсутні таблиці під час запуску застосунку."""
    initialize_database()
    yield


app = FastAPI(
    title=f"ЛР №3 — {config.SUBJECT_AREA}",
    description=config.describe(),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(categories.router)
app.include_router(records.router)


@app.get("/ping", tags=["service"], summary="Перевірка доступності")
def ping() -> dict:
    """Повертає стан доступності API."""
    return {"status": "ok"}


@app.get("/student", tags=["service"], summary="Дані студента")
def student() -> dict:
    """Повертає ПІБ, групу та номер варіанта."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }
