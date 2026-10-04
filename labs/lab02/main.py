"""Головний CLI лабораторної роботи №2."""

from __future__ import annotations

import argparse
import sys

from labs.lab02 import task1, task2


def build_parser() -> argparse.ArgumentParser:
    """Створює парсер команд demo та analyze."""
    parser = argparse.ArgumentParser(
        prog="python -m labs.lab02.main",
        description=(
            "Лабораторна робота №2: ООП (Завдання 1) та CLI-утиліта "
            "для аналізу SSH auth.log (Завдання 2, Варіант 4)."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser(
        "demo",
        help="Демонстрація ООП: користувачі, сесії та журнал аудиту.",
    )
    analyze = subparsers.add_parser(
        "analyze",
        help="Аналіз auth.log і виявлення підбору паролів (bruteforce).",
    )
    task2.add_arguments(analyze)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Запускає обрану підкоманду та повертає код виходу."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "demo":
        task1.demo()
        return 0
    return task2.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
