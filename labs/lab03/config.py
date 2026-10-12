"""Налаштування предметної області варіанта 4."""

from shared.student import VARIANT_NUMBER

SUBJECT_AREA = "Облік подій автентифікації"
UNIT = "events"
UNIT_DESCRIPTION = "кількість подій у спостереженні"

VALUE_MIN = 0
VALUE_MAX: int | None = None
THRESHOLD = 20

ALLOWED_STATUSES = ("new", "in_progress", "done")

MAX_TITLE_LENGTH = 120
MAX_CODE_LENGTH = 40
MAX_CATEGORY_NAME_LENGTH = 40

BULK_MIN_ITEMS = 1
BULK_MAX_ITEMS = 100

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


def describe() -> str:
    """Повертає короткий опис обмежень варіанта для документації."""
    bounds = f">= {VALUE_MIN}"
    if VALUE_MAX is not None:
        bounds += f" і <= {VALUE_MAX}"
    return (
        f"Варіант {VARIANT_NUMBER}: {SUBJECT_AREA}. "
        f"value — {UNIT} ({UNIT_DESCRIPTION}), {bounds}. "
        f"Поріг реагування: {THRESHOLD}."
    )
