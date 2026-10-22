# Лабораторная работа 2. Потоковыйанализатор файлов

Шеляг Макар Витальевич М8О-102БВ-26
___

## Возможности

- **`analyze`** — анализирует события из файлов CSV и JSONL.
- **Статистика событий:**
  - общее количество событий;
  - количество событий каждого уровня: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`;
  - количество событий по источникам;
  - пять источников с наибольшим количеством ошибок уровней `ERROR` и `CRITICAL`;
  - минимальная и максимальная временные метки.
- **Обработка нескольких файлов** — объединяет статистику из нескольких файлов в один отчёт.
- **Пропуск некорректных строк** — режим `--skip-invalid` позволяет продолжить обработку файла и учитывает количество пропусков.
- **Два формата отчёта** — JSON и CSV.
- **Реестр парсеров** — позволяет регистрировать обработчики новых форматов без изменения основной логики анализа.

## Установка

Нужен Python 3.10 или новее.

**Windows (PowerShell)**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Если в `pyproject.toml` зависимости уже описаны полностью, установка через `pip install -e .` может быть достаточной.

## Использование

```bash
python -m streamstats --help
python -m streamstats analyze --help
python -m streamstats analyze INPUT [INPUT ...] --format csv|jsonl
```

Основные аргументы:

- `INPUT` — один или несколько входных файлов.
- `--format` — формат входных файлов: `csv` или `jsonl`.
- `--output` — путь для сохранения отчёта.
- `--report-format` — формат отчёта: `json` или `csv`. По умолчанию `json`.
- `--skip-invalid` — пропускать некорректные записи вместо остановки на первой ошибке.

### Примеры

Анализ CSV-файла с выводом отчёта в терминал:

```powershell
python -m streamstats analyze events.csv --format csv
```

Анализ нескольких JSONL-файлов с сохранением результата:

```powershell
python -m streamstats analyze app.jsonl errors.jsonl --format jsonl --output report.json
```

Сохранение отчёта в CSV:

```powershell
python -m streamstats analyze events.jsonl --format jsonl --report-format csv --output report.csv
```

Пропуск некорректных строк:

```powershell
python -m streamstats analyze events.csv --format csv --skip-invalid --output report.json
```

## Формат входных данных

Каждое событие должно содержать четыре поля:

| Поле | Описание |
|---|---|
| `timestamp` | Временная метка в формате ISO 8601 |
| `level` | Уровень события |
| `source` | Непустое название источника |
| `message` | Текст сообщения |

Пример CSV:

```csv
timestamp,level,source,message
2026-10-22T10:00:00,INFO,api,Application started
2026-10-22T10:01:00,ERROR,database,Connection failed
```

Пример JSONL:

```jsonl
{"timestamp":"2026-10-22T10:00:00","level":"INFO","source":"api","message":"Application started"}
{"timestamp":"2026-10-22T10:01:00","level":"ERROR","source":"database","message":"Connection failed"}
```

Каждая строка JSONL содержит отдельный JSON-объект. Для CSV первая строка содержит названия столбцов.

## Структура проекта

```text
src/streamstats/
├── __init__.py
├── __main__.py      # CLI: аргументы и запуск анализа
├── models.py        # модель события Event
├── parsers.py       # чтение, проверка и разбор файлов
├── analysis.py      # расчёт статистики
├── report.py        # формирование JSON- и CSV-отчётов
└── errors.py        # исключения проекта

tests/
├── test_parsers.py
├── test_analysis.py
├── test_report.py
├── test_cli.py
└── test_registry.py
```

## Как работает анализатор

**1. Чтение данных.** В зависимости от выбранного формата используется соответствующий парсер. Он последовательно читает файл и преобразует записи в объекты `Event`.

**2. Проверка событий.** Проверяются наличие обязательных полей, типы значений, допустимый уровень события и корректность временной метки. Некорректные записи приводят к ошибке либо пропускаются при включённом `--skip-invalid`.

**3. Расчёт статистики.** Функция `analyze_events` принимает последовательность событий и обновляет счётчики. События не требуется сохранять в общий список.

**4. Формирование отчёта.** Полученная статистика передаётся в функцию записи JSON или CSV. Повторный анализ данных не выполняется.

**5. Завершение программы.** При успешной обработке возвращается код `0`. При перехваченной ошибке обработки или чтения возвращается код `2`.


## Тесты и проверки

```bash
python -m pytest
ruff check .
mypy src tests
python -m streamstats --help
python -m streamstats analyze --help
```

Тесты проверяют парсеры, расчёт статистики, запись отчётов, обработку некорректных данных, работу реестра и взаимодействие компонентов через CLI.

Отдельно проверяются пустые файлы, несколько входных файлов, Unicode, режим пропуска некорректных записей и попытки повторной регистрации парсера.

## Дополнительные задания

- **CSV-отчёт** — реализована запись рассчитанной статистики в CSV.
- **Реестр парсеров** — добавлены `PARSERS` и `register_parser()` для регистрации обработчиков новых форматов.

