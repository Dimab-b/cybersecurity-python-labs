"""Завдання 3: Хешування, CSV-база та JSON-логування."""

import csv
import functools
import hashlib
import json
import os
import sys
from datetime import datetime

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

HASH_ALGORITHM = "sha512"
MIN_PASSWORD_LENGTH = 14
PERSONAL_SALT = f"{VARIANT_NUMBER:05d}"
DEFAULT_SALT = "00000"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
LOG_JSON = os.path.join(DATA_DIR, "log.json")

USERS_TO_REGISTER = (
    ("alice", "AliceSecure#2023"),
    ("bob", "Bob@StrongPass99"),
    ("carol", "Carol!Safely2024"),
    ("dave", "Dave#Protect2023"),
    ("erin", "Erin@Defense2025"),
    ("frank", "Frank$Secure2023"),
    ("grace", "Grace!Shield2024"),
    ("heidi", "Heidi@Access2023"),
    ("ivan", "Ivan#Privacy2025"),
    ("judy", "Judy!Secret2024"),
)


class ValidationError(Exception):
    """Виняток, що виникає при невідповідності пароля вимогам."""


def generate_hash(password: str, salt: str = DEFAULT_SALT) -> str:
    """Повертає hex-хеш від конкатенації пароля та солі."""
    if not password or not salt:
        raise ValueError("Пароль і сіль не можуть бути порожніми.")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль має містити щонайменше {MIN_PASSWORD_LENGTH} символів."
        )
    data = (password + salt).encode("utf-8")
    return hashlib.new(HASH_ALGORITHM, data).hexdigest()


def create_user(username: str, password: str) -> tuple:
    """Створює запис користувача у вигляді (логін, хеш пароля)."""
    password_hash = generate_hash(password, PERSONAL_SALT)
    return (username, password_hash)


def create_users(users_list):
    """Створює CSV-базу користувачів зі списку (логін, пароль)."""
    created = []
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            for username, password in users_list:
                try:
                    user = create_user(username, password)
                except ValidationError as error:
                    print(f"Пропущено користувача '{username}': {error}")
                    continue
                writer.writerow(user)
                created.append(user)
    except PermissionError as error:
        print(f"Помилка доступу при створенні файлу {USERS_CSV}: {error}")
    except IOError as error:
        print(f"Помилка введення/виведення при записі в {USERS_CSV}: {error}")

    return created


def read_users_db():
    """Зчитує CSV-базу користувачів у список кортежів."""
    users_db = []
    try:
        with open(USERS_CSV, "r", newline="", encoding="utf-8") as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if len(row) == 2:
                    users_db.append((row[0], row[1]))
    except FileNotFoundError:
        print(f"Помилка: Файл бази даних '{USERS_CSV}' не знайдено.")
    except PermissionError as error:
        print(f"Немає доступу до читання файлу '{USERS_CSV}': {error}")
    except IOError as error:
        print(f"Помилка введення/виведення при читанні '{USERS_CSV}': {error}")

    return users_db


def print_users_table(users_db):
    """Виводить користувачів із бази у табличному вигляді."""
    if not users_db:
        print("База даних порожня або не вдалося зчитати записи.")
        return

    print(f"{'№':<4}{'Логін':<14}{'Хеш пароля'}")
    print("-" * 66)
    for index, (username, password_hash) in enumerate(users_db, 1):
        print(f"{index:<4}{username:<14}{password_hash}")
    print("-" * 66)
    print(f"Усього користувачів у базі: {len(users_db)}")


def _write_log_event(username, result):
    """Додає один запис про подію входу у файл log.json."""
    event = {
        "event": "login",
        "user": username,
        "result": result,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "args": [],
        "kwargs": {},
    }
    events = []
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        if os.path.exists(LOG_JSON):
            try:
                with open(LOG_JSON, "r", encoding="utf-8") as log_file:
                    events = json.load(log_file)
            except (json.JSONDecodeError, OSError):
                print("Застереження: Помилка зчитування журналу")
                events = []

        events.append(event)
        with open(LOG_JSON, "w", encoding="utf-8") as log_file:
            json.dump(events, log_file, ensure_ascii=False, indent=2)
    except (PermissionError, IOError) as error:
        print(f"Помилка запису у файл журналу '{LOG_JSON}': {error}")


def log_event(func):
    """Декоратор, що журналює кожну спробу входу у log.json."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        username = args[0] if args else kwargs.get("username", "")
        try:
            result = func(*args, **kwargs)
        except (ValueError, ValidationError):
            _write_log_event(username, "failure")
            raise
        _write_log_event(username, "success" if result else "failure")
        return result

    return wrapper


@log_event
def login(username: str, password: str) -> bool:
    """Перевіряє автентифікацію користувача за логіном і паролем."""
    if not username or not password:
        raise ValueError("Логін і пароль не можуть бути порожніми.")

    users_db = read_users_db()
    for stored_login, stored_hash in users_db:
        if stored_login == username:
            expected = generate_hash(password, PERSONAL_SALT)
            return stored_hash == expected
    return False


def main():
    """Демонструє реєстрацію, читання бази та автентифікацію."""
    print("=" * 66)
    print(
        f"Завдання 3. Варіант {VARIANT_NUMBER}. {STUDENT_NAME} ({GROUP_NAME})"
    )
    print(
        f"Алгоритм хешування: {HASH_ALGORITHM}, "
        f"мінімальна довжина пароля: {MIN_PASSWORD_LENGTH}"
    )
    print(f"Персональна сіль: {PERSONAL_SALT}")
    print("=" * 66)

    print("\n[1] Реєстрація користувачів...")
    created = create_users(USERS_TO_REGISTER)
    print(f"Успішно створено користувачів: {len(created)}")

    print("\n[2] Читання бази користувачів...")
    users_db = read_users_db()
    print_users_table(users_db)

    print("\n[3] Перевірка автентифікації...")
    attempts = [
        ("alice", "AliceSecure#2023"),
        ("alice", "WrongPassword#123"),
        ("unknown", "AliceSecure#2023"),
    ]
    for username, password in attempts:
        try:
            success = login(username, password)
            status = "успішно" if success else "відхилено"
            print(f"login('{username}') -> {status}")
        except ValidationError as error:
            print(f"login('{username}') -> помилка валідації: {error}")
        except ValueError as error:
            print(f"login('{username}') -> помилка: {error}")

    print("\n[4] Демонстрація обробки винятків...")
    try:
        generate_hash("short")
    except ValidationError as error:
        print(f"ValidationError: {error}")
    try:
        generate_hash("", PERSONAL_SALT)
    except ValueError as error:
        print(f"ValueError: {error}")

    print(f"\nЖурнал подій збережено у: {LOG_JSON}")


if __name__ == "__main__":
    main()
