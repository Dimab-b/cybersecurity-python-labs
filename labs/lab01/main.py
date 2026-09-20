"""Головний файл лабораторної роботи №1."""

import os
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
)

from labs.lab01 import task1, task2, task3


def main():
    """Запускає всі три завдання лабораторної роботи."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    task1.main()
    print()
    task2.main()
    print()
    task3.main()


if __name__ == "__main__":
    main()
