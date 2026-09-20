"""Завдання 1: Комплексний аналізатор надійності паролів."""

import os
import random
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

PASSWORDS = [
    "Security@2023",
    "pass",
    "MyStr0ng#Key",
    "root",
    "Advanc3d@Pass",
    "user",
    "Protec7!Pass",
    "1234",
    "Elite@Secur1ty",
    "admin123",
]

CRITERIA = {
    "min_length": 7,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

FORBIDDEN_PASSWORDS = {
    "pass",
    "root",
    "user",
    "1234",
    "admin123",
    "password",
}

DUPLICATES_COUNT = 3


def add_random_duplicates(passwords):
    """Додає дублікати випадкових паролів у кінець списку."""
    duplicated = list(passwords)
    if not passwords:
        return duplicated
    for _ in range(DUPLICATES_COUNT):
        index = random.randrange(len(passwords))
        duplicated.append(passwords[index])
    return duplicated


def analyze_character_groups(password):
    """Повертає словник із наявністю груп символів у паролі."""
    return {
        "length": len(password) >= CRITERIA["min_length"],
        "digit": any(char.isdigit() for char in password),
        "upper": any(char.isupper() for char in password),
        "lower": any(char.islower() for char in password),
        "special": any(not char.isalnum() for char in password),
    }


def evaluate_password(password, all_passwords):
    """Оцінює надійність одного пароля за алгоритмом роботи."""
    min_length = CRITERIA["min_length"]
    if password in FORBIDDEN_PASSWORDS or len(password) < min_length:
        return "Заборонений"

    groups = analyze_character_groups(password)
    requirements = {
        "length": True,
        "digit": CRITERIA["require_digits"],
        "upper": CRITERIA["require_upper"],
        "special": CRITERIA["require_special"],
    }
    required_names = [name for name, needed in requirements.items() if needed]
    met = sum(1 for name in required_names if groups[name])
    total = len(required_names)
    long_enough = len(password) >= min_length + 4
    unique = all_passwords.count(password) == 1

    if met == total and long_enough and unique:
        return "Дуже сильний"
    if met == total:
        return "Сильний"
    if met >= 2:
        return "Середній"
    return "Слабкий"


def print_report(passwords, verdicts):
    """Виводить результати аналізу у табличному вигляді."""
    print("=" * 66)
    print(
        f"Завдання 1. Варіант {VARIANT_NUMBER}. {STUDENT_NAME} ({GROUP_NAME})"
    )
    print("=" * 66)
    print(f"{'№':<4}{'Пароль':<22}{'Оцінка':<18}{'Унікальний'}")
    print("-" * 66)
    for index, (password, verdict) in enumerate(zip(passwords, verdicts), 1):
        unique = "так" if passwords.count(password) == 1 else "ні"
        print(f"{index:<4}{password:<22}{verdict:<18}{unique}")
    print("-" * 66)
    print(f"Усього проаналізовано паролів: {len(passwords)}")


def main():
    """Виконує повний аналіз списку паролів варіанта."""
    all_passwords = add_random_duplicates(PASSWORDS)
    verdicts = [
        evaluate_password(password, all_passwords)
        for password in all_passwords
    ]
    print_report(all_passwords, verdicts)


if __name__ == "__main__":
    main()
