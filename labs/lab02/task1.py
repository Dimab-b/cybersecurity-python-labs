"""Завдання 1: модель користувача, безпечної сесії та журналу аудиту."""

from __future__ import annotations

import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 200_000
SALT_SIZE = 16
SESSION_TIMEOUT_SEC = 900

ACTION_LOGIN_SUCCESS = "login_success"
ACTION_LOGIN_FAILURE = "login_failure"
ACTION_LOGOUT = "logout"

EMAIL_PATTERN = re.compile(
    r"^[A-Za-z][A-Za-z0-9_]{2,63}@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
)


def utc_now() -> datetime:
    """Повертає поточний час у UTC із часовим поясом."""
    return datetime.now(timezone.utc)


class User:
    """Звичайний користувач системи з хешованим паролем."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str,
        active: bool = True,
    ) -> None:
        self.username = username
        self.role = role
        self.active = active
        self.email = email
        self.__password_hash: bytes | None = None
        self.__password_salt: bytes | None = None

    @property
    def email(self) -> str:
        """Повертає e-mail користувача."""
        return self.__email

    @email.setter
    def email(self, value: str) -> None:
        """Встановлює e-mail після перевірки формату регулярним виразом."""
        if not isinstance(value, str) or not EMAIL_PATTERN.match(value):
            raise ValueError(f"Некоректний формат e-mail: {value!r}")
        self.__email = value

    def set_password(self, password: str) -> bool:
        """Хешує пароль із випадковою сіллю через PBKDF2-HMAC-SHA256."""
        if not isinstance(password, str) or not password:
            raise ValueError("Пароль має бути непорожнім рядком")
        salt = os.urandom(SALT_SIZE)
        digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
        )
        self.__password_salt = salt
        self.__password_hash = digest
        return True

    def check_password(self, password: str) -> bool:
        """Перевіряє пароль, порівнюючи хеші у сталий час."""
        if self.__password_hash is None or self.__password_salt is None:
            return False
        if not isinstance(password, str):
            return False
        digest = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            self.__password_salt,
            PBKDF2_ITERATIONS,
        )
        return hmac.compare_digest(digest, self.__password_hash)

    def deactivate(self) -> None:
        """Позначає обліковий запис як неактивний."""
        self.active = False

    def __str__(self) -> str:
        state = "активний" if self.active else "неактивний"
        return (
            f"User(логін={self.username}, email={self.email}, "
            f"роль={self.role}, стан={state})"
        )


class Admin(User):
    """Адміністратор, що успадковує користувача та має права доступу."""

    def __init__(
        self,
        username: str,
        email: str,
        role: str = "admin",
        active: bool = True,
        permissions: set[str] | None = None,
    ) -> None:
        super().__init__(username, email, role, active)
        self.permissions: set[str] = set(permissions) if permissions else set()

    def grant_permission(self, permission: str) -> None:
        """Додає дозвіл адміністратору."""
        self.permissions.add(permission)

    def revoke_permission(self, permission: str) -> None:
        """Прибирає дозвіл адміністратора."""
        self.permissions.discard(permission)

    def has_permission(self, permission: str) -> bool:
        """Перевіряє наявність дозволу."""
        return permission in self.permissions

    def __str__(self) -> str:
        rights = ", ".join(sorted(self.permissions)) or "без прав"
        return f"Admin(логін={self.username}, права: {rights})"


class Session:
    """Сесія користувача з відстеженням часу останньої активності."""

    def __init__(
        self,
        ip: str,
        login_time: datetime | None = None,
    ) -> None:
        self.ip = ip
        self.login_time = login_time or utc_now()
        self.last_activity = self.login_time

    def touch(self) -> None:
        """Оновлює час останньої активності до поточного моменту."""
        self.last_activity = utc_now()

    def is_active(self, timeout_sec: int) -> bool:
        """Перевіряє, чи не минув час неактивності сесії."""
        if not isinstance(timeout_sec, int) or timeout_sec <= 0:
            raise ValueError("timeout_sec має бути додатним цілим числом")
        elapsed = utc_now() - self.last_activity
        return elapsed <= timedelta(seconds=timeout_sec)

    def __str__(self) -> str:
        return (
            f"Session(ip={self.ip}, login_time={self.login_time.isoformat()})"
        )


@dataclass
class AuditRecord:
    """Один запис журналу аудиту."""

    timestamp: datetime
    username: str
    action: str


class AuditLog:
    """Журнал подій із записами у вигляді dataclass."""

    def __init__(self) -> None:
        self.records: list[AuditRecord] = []

    def add_log(self, username: str, action: str) -> None:
        """Додає подію з поточною міткою часу UTC."""
        self.records.append(AuditRecord(utc_now(), username, action))

    def show_all(self) -> None:
        """Виводить усі записи журналу."""
        if not self.records:
            print("Журнал порожній.")
            return
        for record in self.records:
            stamp = record.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            print(f"  [{stamp}] {record.username}: {record.action}")


class UserAccount:
    """Обліковий запис: композиція користувача, сесії та журналу."""

    _FIELDS = {
        "username": str,
        "email": str,
        "role": str,
        "active": bool,
    }

    def __init__(
        self,
        user: User,
        session: Session | None = None,
        audit_log: AuditLog | None = None,
    ) -> None:
        self.user = user
        self.session = session
        self.audit_log = audit_log or AuditLog()

    def login(self, username: str, password: str, ip: str) -> bool:
        """Виконує вхід: перевіряє активність і пароль, створює сесію."""
        if not self.user.active:
            self.audit_log.add_log(username, ACTION_LOGIN_FAILURE)
            return False
        if username != self.user.username:
            self.audit_log.add_log(username, ACTION_LOGIN_FAILURE)
            return False
        if not self.user.check_password(password):
            self.audit_log.add_log(username, ACTION_LOGIN_FAILURE)
            return False
        self.session = Session(ip)
        self.session.touch()
        self.audit_log.add_log(username, ACTION_LOGIN_SUCCESS)
        return True

    def is_authenticated(self) -> bool:
        """Перевіряє наявність активної сесії у межах таймауту."""
        if self.session is None:
            return False
        return self.session.is_active(SESSION_TIMEOUT_SEC)

    def logout(self) -> bool:
        """Завершує сесію та фіксує вихід у журналі."""
        if self.session is None:
            return False
        self.session = None
        self.audit_log.add_log(self.user.username, ACTION_LOGOUT)
        return True

    def __getitem__(self, key: str) -> object:
        """Дозволяє читати атрибути через account["user"], account["email"]."""
        if key == "user":
            return self.user
        if key in self._FIELDS:
            return getattr(self.user, key)
        raise KeyError(f"Недозволений ключ: {key!r}")

    def __setitem__(self, key: str, value: object) -> None:
        """Дозволяє запис атрибутів із перевіркою типу значення."""
        if key == "user":
            if not isinstance(value, User):
                raise TypeError("account['user'] має бути об'єктом User")
            self.user = value
            return
        if key not in self._FIELDS:
            raise KeyError(f"Недозволений ключ: {key!r}")
        expected = self._FIELDS[key]
        if not isinstance(value, expected):
            raise TypeError(
                f"Для ключа {key!r} очікується {expected.__name__}"
            )
        setattr(self.user, key, value)


def _print_header(title: str) -> None:
    print("=" * 66)
    print(title)
    print("=" * 66)


def demo() -> None:
    """Демонструє роботу всіх класів Завдання 1."""
    _print_header(
        f"Завдання 1. Варіант {VARIANT_NUMBER}. {STUDENT_NAME} ({GROUP_NAME})"
    )

    user = User("d_batih", "d_batih@example.com", "analyst")
    user.set_password("S3cur3#Pass")
    account = UserAccount(user)
    print(f"Створено користувача: {user}")

    print("\n1) Успішний вхід:")
    success = account.login("d_batih", "S3cur3#Pass", "192.0.2.10")
    print(
        f"   login() -> {success}, is_authenticated()="
        f"{account.is_authenticated()}"
    )

    print("\n2) Невдалий вхід (хибний пароль):")
    account.logout()
    failed = account.login("d_batih", "wrong-password", "192.0.2.10")
    print(f"   login() -> {failed}")

    print("\n3) Зміна e-mail із валідацією:")
    account["email"] = "new_mail@example.com"
    print(f"   новий email: {account['email']}")
    try:
        account["email"] = "wrong-email"
    except ValueError as error:
        print(f"   ValueError: {error}")

    print("\n4) Права адміністратора:")
    admin = Admin("root_admin", "admin@example.com")
    admin.grant_permission("read_logs")
    admin.grant_permission("block_ips")
    admin.revoke_permission("read_logs")
    print(f"   {admin}")
    print(
        f"   has_permission('block_ips')={admin.has_permission('block_ips')}"
    )

    print("\n5) Завершення сесії за таймаутом:")
    account.login("d_batih", "S3cur3#Pass", "192.0.2.10")
    account.session.last_activity = utc_now() - timedelta(
        seconds=SESSION_TIMEOUT_SEC + 1
    )
    print(f"   is_authenticated() після таймауту={account.is_authenticated()}")

    print("\n6) Вихід із системи:")
    account.logout()
    print(
        f"   session={account.session}, "
        f"is_authenticated()={account.is_authenticated()}"
    )

    print("\n7) Журнал аудиту (AuditLog):")
    account.audit_log.show_all()

    print("\n8) Захищені ключі недоступні через інтерфейс словника:")
    try:
        account["__password_hash"]
    except KeyError as error:
        print(f"   KeyError: {error}")
    try:
        account["active"] = "yes"
    except TypeError as error:
        print(f"   TypeError: {error}")
