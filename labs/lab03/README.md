# Лабораторна робота №3 — FastAPI + SQLite

**Варіант 4:** «Облік подій автентифікації».

Сервіс зберігає підсумки спостереження за автентифікацією. Один запис
описує **кількість подій** певного типу за навчальний інтервал, а `status`
визначає стан перевірки спостереження.

| Поле | Опис |
| --- | --- |
| `id` | первинний ключ (створює SQLite) |
| `code` | унікальний код запису, `V04-01` … |
| `title` | назва, напр. `Інтервал автентифікації 01` |
| `category_id` | зовнішній ключ на `categories.id` |
| `value` | кількість подій (`INTEGER`, `>= 0`) |
| `status` | `new` / `in_progress` / `done` |

- **Одиниця вимірювання:** `events` (кількість подій у спостереженні).
- **Поріг реагування:** `20`.
- **Категорії:** `failed_login`, `blocked_account`, `mfa_failure`.

## 1. Встановлення залежностей

З кореня репозиторію, у віртуальному середовищі (Python 3.10+):

```bash
pip install -r requirements.txt
```

## 2. Створення бази та початкове заповнення

```bash
python -m labs.lab03.database   # створити таблиці (за потреби)
python -m labs.lab03.seed       # 3 категорії та 8 записів
```

`seed` ініціалізує базу сам. Повторний запуск не додає дублікатів.

## 3. Запуск API

```bash
uvicorn labs.lab03.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI: http://127.0.0.1:8000/openapi.json

## 4. Маршрути

| Метод | Шлях | Призначення | Код успіху |
| --- | --- | --- | --- |
| GET | `/ping` | доступність API | 200 |
| GET | `/student` | ПІБ, група, варіант | 200 |
| GET | `/categories` | список категорій | 200 |
| POST | `/categories` | створити категорію | 201 |
| DELETE | `/categories/{id}` | видалити порожню | 204 |
| GET | `/records` | список із фільтрами | 200 |
| GET | `/records/{id}` | один запис | 200 |
| POST | `/records` | створити запис | 201 |
| PUT | `/records/{id}` | повна заміна полів | 200 |
| DELETE | `/records/{id}` | видалити запис | 204 |
| POST | `/records/bulk` | пакет (1–100) атомарно | 201 |

Помилки: `404` — немає запису/категорії; `409` — дублікат `code`/назви,
видалення непорожньої категорії; `422` — некоректна модель або параметр;
`204` — без тіла відповіді.

### Параметри `GET /records`

`category_id` (`int > 0`), `status` (`new|in_progress|done`),
`min_value` (`int >= 0`), `q` (підрядок у `title`, 1–120 символів),
`limit` (1–100, типово 20), `offset` (`>= 0`). Фільтри об'єднуються через
`AND`, результат сортується за `id`.

## 5. Приклади запитів

```bash
curl -i http://127.0.0.1:8000/ping
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5"
curl -i -X POST http://127.0.0.1:8000/records \
  -H "Content-Type: application/json" \
  -d '{"code":"V04-TEST","title":"Тестовий інтервал","category_id":1,"value":7,"status":"new"}'
curl -i -X POST http://127.0.0.1:8000/records/bulk \
  -H "Content-Type: application/json" \
  -d '[{"code":"V04-B1","title":"Пакет перший","category_id":1,"value":4,"status":"new"},
       {"code":"V04-B2","title":"Пакет другий","category_id":2,"value":5,"status":"new"}]'
```

## 6. Структура та відтворення

```
labs/lab03/
├── main.py        # FastAPI-застосунок
├── database.py    # з'єднання та ініціалізація
├── repository.py  # параметризовані SQL-запити
├── schemas.py     # Pydantic-моделі
├── config.py      # одиниця, поріг, обмеження варіанта
├── seed.py        # початкове заповнення
├── schema.sql     # надана схема таблиць
├── routers/       # categories.py, records.py
└── data/
    ├── seed.json      # навчальні дані (у Git)
    └── lab3.sqlite3   # файл бази (не в Git)
```

## 7. Контроль якості

```bash
ruff check labs/lab03
ruff format --check labs/lab03
```
