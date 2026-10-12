"""Завдання 2 (Варіант 4): парсер SSH auth.log та детектор bruteforce."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import re

from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

LAB_DIR = Path(__file__).resolve().parent
DEFAULT_AUTH_LOG = LAB_DIR / "data" / "data_v04" / "auth.log"
DEFAULT_OUTPUT = LAB_DIR / "data" / "blocklist_ips.json"
DEFAULT_TOP = 3

AUTH_PATTERN = re.compile(
    r"^(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+sshd\[\d+\]:\s+"
    r"(?P<result>Failed|Accepted)\s+password\s+for\s+"
    r"(?:(?P<invalid>invalid user)\s+)?(?P<user>\S+)\s+"
    r"from\s+(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+"
    r"port\s+\d+"
)

logger = logging.getLogger("lab02.task2")


@dataclass
class AuthEvent:
    """Одна розібрана подія автентифікації SSH."""

    timestamp: datetime
    host: str
    username: str
    ip: str
    result: str
    invalid_user: bool = False

    @property
    def failed(self) -> bool:
        """Чи є подія невдалою спробою входу."""
        return self.result == "Failed"


@dataclass
class BruteforceFinding:
    """Результат виявлення підбору пароля для однієї IP-адреси."""

    ip: str
    failures_in_window: int
    total_failures: int
    window_from: datetime
    window_to: datetime
    target_users: list[str] = field(default_factory=list)


def configure_logging(log_file: Path | None, level: str) -> None:
    """Налаштовує консольне та (за потреби) файлове логування."""
    logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(levelname)s] %(message)s")

    console = logging.StreamHandler()
    console.setLevel(getattr(logging, level.upper(), logging.INFO))
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file is not None:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except (PermissionError, OSError) as err:
            logger.error(
                "Не вдалося створити або відкрити файл логу %s: %s",
                log_file,
                err,
            )


def parse_auth_log(path: Path, year: int | None = None) -> list[AuthEvent]:
    """Розбирає файл auth.log і повертає список подій."""
    if not path.exists():
        raise FileNotFoundError(f"Файл журналу не знайдено: {path}")
    if not path.is_file():
        raise IsADirectoryError(f"Вказаний шлях є директорією, а не файлом: {path}")

    reference_year = year or datetime.now().year
    events: list[AuthEvent] = []
    logger.info("Analyzing authentication events in %s...", path)

    try:
        with path.open(encoding="utf-8", errors="replace") as stream:
            for line_number, raw_line in enumerate(stream, 1):
                match = AUTH_PATTERN.match(raw_line.strip())
                if match is None:
                    logger.debug(
                        "Рядок %d пропущено (не розпізнано).", line_number
                    )
                    continue

                try:
                    parsed = datetime.strptime(
                        f"{reference_year} {match['timestamp']}",
                        "%Y %b %d %H:%M:%S",
                    )
                except ValueError as err:
                    logger.warning(
                        "Некоректна дата у рядку %d: %s", line_number, err
                    )
                    continue

                events.append(
                    AuthEvent(
                        timestamp=parsed,
                        host=match["host"],
                        username=match["user"],
                        ip=match["ip"],
                        result=match["result"],
                        invalid_user=bool(match["invalid"]),
                    )
                )
    except PermissionError:
        logger.error("Відмовлено в доступі при читанні файлу: %s", path)
        raise
    except OSError as err:
        logger.error("Помилка вводу/виводу при читанні файлу %s: %s", path, err)
        raise

    return events


def _find_max_window(
    failures: list[tuple[datetime, str]], window: timedelta
) -> tuple[int, datetime | None, datetime | None, list[str]]:
    """Знаходить вікно з максимальною кількістю невдалих спроб."""
    failures = sorted(failures)
    best_count = 0
    best_from: datetime | None = None
    best_to: datetime | None = None
    best_users: list[str] = []
    left = 0
    for right, (moment, _) in enumerate(failures):
        while moment - failures[left][0] > window:
            left += 1
        count = right - left + 1
        if count > best_count:
            best_count = count
            best_from = failures[left][0]
            best_to = moment
            best_users = sorted(
                {name for _, name in failures[left : right + 1]}
            )
    return best_count, best_from, best_to, best_users


def detect_bruteforce(
    events: list[AuthEvent], threshold: int, window_min: int
) -> list[BruteforceFinding]:
    """Агрегує невдалі спроби за часовим вікном і повертає загрози."""
    if threshold <= 0:
        raise ValueError("threshold має бути додатним")
    if window_min <= 0:
        raise ValueError("window_min має бути додатним")

    window = timedelta(minutes=window_min)
    failures_by_ip: defaultdict[str, list[tuple[datetime, str]]] = defaultdict(
        list
    )
    for event in events:
        if event.failed:
            failures_by_ip[event.ip].append((event.timestamp, event.username))

    findings: list[BruteforceFinding] = []
    for ip, entries in failures_by_ip.items():
        count, start, end, users = _find_max_window(entries, window)
        if count >= threshold and start is not None and end is not None:
            findings.append(
                BruteforceFinding(
                    ip=ip,
                    failures_in_window=count,
                    total_failures=len(entries),
                    window_from=start,
                    window_to=end,
                    target_users=users,
                )
            )
    findings.sort(key=lambda item: item.failures_in_window, reverse=True)
    return findings


def build_report(
    events: list[AuthEvent],
    findings: list[BruteforceFinding],
    threshold: int,
    window_min: int,
    source: Path,
) -> dict:
    """Формує словник підсумкового звіту."""
    failed = [event for event in events if event.failed]
    accepted = [event for event in events if not event.failed]
    moments = [event.timestamp for event in events]
    failed_counter = Counter(event.ip for event in failed)

    time_from = min(moments).isoformat() if moments else None
    time_to = max(moments).isoformat() if moments else None

    serialize = lambda value: value.isoformat()  # noqa: E731
    findings_json = []
    for finding in findings:
        record = asdict(finding)
        record["window_from"] = serialize(finding.window_from)
        record["window_to"] = serialize(finding.window_to)
        findings_json.append(record)

    return {
        "variant": VARIANT_NUMBER,
        "student": STUDENT_NAME,
        "group": GROUP_NAME,
        "source": str(source),
        "total_lines": len(events),
        "failed_total": len(failed),
        "accepted_total": len(accepted),
        "time_from": time_from,
        "time_to": time_to,
        "threshold": threshold,
        "window_minutes": window_min,
        "top_failed_ips": [
            {"ip": ip, "failures": amount}
            for ip, amount in failed_counter.most_common(DEFAULT_TOP)
        ],
        "bruteforce": findings_json,
        "blocklist": [finding.ip for finding in findings],
    }


def save_report(report: dict, output: Path) -> None:
    """Зберігає звіт у JSON-файл із захистом від помилок запису."""
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(report, ensure_ascii=False, indent=2)
        output.write_text(content, encoding="utf-8")
    except PermissionError:
        logger.error("Відмовлено в доступі при записі звіту у файл: %s", output)
        raise
    except (TypeError, ValueError) as err:
        logger.error("Помилка серіалізації даних у JSON: %s", err)
        raise
    except OSError as err:
        logger.error(
            "Помилка вводу/виводу при збереженні звіту в %s: %s", output, err
        )
        raise


def print_summary(report: dict, findings: list[BruteforceFinding]) -> None:
    """Виводить підсумок аналізу в консоль."""
    print("=" * 66)
    print(
        f"=== SSH Bruteforce Detection Results (Variant "
        f"{report['variant']}) ==="
    )
    print("=" * 66)
    print(
        f"Failed Attempts Threshold: >= {report['threshold']} attempts "
        f"in {report['window_minutes']} minutes"
    )
    if not findings:
        print("Підозрілих IP-адрес не виявлено.")
    for finding in findings:
        users = ", ".join(finding.target_users)
        logger.error(
            "[ALERT] Bruteforce Detected! IP: %s | Total Failures: %d | "
            "Target Users: %s",
            finding.ip,
            finding.total_failures,
            users,
        )
    print("\n=== Top Failed IP Addresses ===")
    for item in report["top_failed_ips"]:
        print(f"{item['ip']:<16} - {item['failures']} failures")
    print("\n=== Recommended Blocklist (IPs) ===")
    if report["blocklist"]:
        for ip in report["blocklist"]:
            print(ip)
    else:
        print("(порожній)")


def run(args: argparse.Namespace) -> int:
    """Точка входу для підкоманди analyze."""
    configure_logging(args.log_file, args.log_level)
    source = Path(args.auth_log)

    logger.info("Loading authentication log from %s...", source)
    try:
        events = parse_auth_log(source)
    except (FileNotFoundError, IsADirectoryError, PermissionError, OSError) as error:
        logger.error("Не вдалося обробити файл: %s", error)
        return 1

    if not events:
        logger.warning("Не знайдено жодної коректної події у файлі.")
        return 1

    findings = detect_bruteforce(events, args.threshold, args.window_min)
    report = build_report(
        events, findings, args.threshold, args.window_min, source
    )
    print_summary(report, findings)

    output = Path(args.output_json)
    try:
        save_report(report, output)
        logger.info("Exported blocklist to %s", output)
    except (PermissionError, OSError, ValueError) as error:
        logger.error("Не вдалося зберегти звіт: %s", error)
        return 1

    return 0


def add_arguments(parser: argparse.ArgumentParser) -> None:
    """Додає аргументи CLI для підкоманди analyze."""
    parser.add_argument(
        "--auth-log",
        default=str(DEFAULT_AUTH_LOG),
        help="Шлях до файлу auth.log (за замовчуванням: дані варіанта 4).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=5,
        help="Поріг невдалих спроб у вікні (за замовчуванням: 5).",
    )
    parser.add_argument(
        "--window-min",
        type=int,
        default=5,
        help="Розмір часового вікна у хвилинах (за замовчуванням: 5).",
    )
    parser.add_argument(
        "--output-json",
        default=str(DEFAULT_OUTPUT),
        help="Шлях до JSON-звіту (за замовчуванням: data/blocklist_ips.json).",
    )
    parser.add_argument(
        "--log-file",
        default=None,
        help="Необов'язковий шлях до файлу журналу роботи утиліти.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Рівень консольного логування (за замовчуванням: INFO).",
    )