"""Завдання 2: Багаторівнева система контролю доступу."""

import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

USERS = {
    "ciso_office": {
        "role": "ciso",
        "clearance": 4,
        "department": "Executive",
        "active": True,
    },
    "threat_hunter": {
        "role": "threat_analyst",
        "clearance": 3,
        "department": "Threat Intel",
        "active": True,
    },
    "junior_dev": {
        "role": "junior_developer",
        "clearance": 2,
        "department": "Development",
        "active": True,
    },
    "visitor_acc": {
        "role": "visitor",
        "clearance": 1,
        "department": "Guest",
        "active": True,
    },
    "legacy_sys": {
        "role": "legacy",
        "clearance": 2,
        "department": "Legacy",
        "active": False,
    },
}

RESOURCES = [
    ("threat_intelligence", 4),
    ("malware_samples", 3),
    ("coding_guidelines", 2),
    ("visitor_wifi", 1),
    ("strategic_plans", 4),
    ("demo_environment", 1),
    ("risk_assessments", 3),
    ("crypto_keys", 4),
    ("api_documentation", 2),
    ("guest_portal", 1),
]

SECURITY_LEVELS = ("Guest", "Employee", "Privileged", "Executive")

BLOCKED_USERS = {"legacy_sys", "malicious_user", "expired_guest"}


def level_to_name(level):
    """Перетворює числовий рівень безпеки у його текстову назву."""
    if 1 <= level <= len(SECURITY_LEVELS):
        return SECURITY_LEVELS[level - 1]
    return f"Невідомий рівень ({level})"


def check_access(username, resource_level):
    """Повертає кортеж (доступ, причина) для користувача та ресурсу."""
    user = USERS.get(username)
    if user is None:
        return False, "User not found"
    if username in BLOCKED_USERS:
        return False, "User is blocked"
    if not user["active"]:
        return False, "Account inactive"
    if user["clearance"] >= resource_level:
        return True, ""
    return False, "Insufficient clearance"


def print_resources():
    """Виводить перелік ресурсів із текстовими рівнями безпеки."""
    print("=" * 66)
    print(
        f"Завдання 2. Варіант {VARIANT_NUMBER}. {STUDENT_NAME} ({GROUP_NAME})"
    )
    print("=" * 66)
    print("Ресурси системи:")
    print(f"{'Ресурс':<24}{'Рівень безпеки'}")
    print("-" * 66)
    for name, level in RESOURCES:
        print(f"{name:<24}{level_to_name(level)}")
    print("-" * 66)


def print_users_overview():
    """Виводить стислий огляд користувачів системи."""
    print("\nКористувачі системи:")
    print(f"{'Логін':<16}{'Роль':<18}{'Відділ':<16}{'Доступ'}")
    print("-" * 66)
    for login, data in USERS.items():
        role = data.get("role", "-")
        department = data.get("department", "-")
        clearance = data.get("clearance", "-")
        print(f"{login:<16}{role:<18}{department:<16}{clearance}")
    print("-" * 66)


def print_access_matrix():
    """Перевіряє доступ кожного користувача до кожного ресурсу."""
    print("\nМатриця доступу:")
    for username in USERS:
        for resource_name, level in RESOURCES:
            allowed, reason = check_access(username, level)
            status = "ALLOW" if allowed else f"DENY ({reason})"
            print(f"user={username} resource={resource_name} -> {status}")


def main():
    """Демонструє роботу системи контролю доступу."""
    print_resources()
    print_users_overview()
    print_access_matrix()


if __name__ == "__main__":
    main()
