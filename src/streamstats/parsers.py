import csv
import json
import logging
from collections.abc import Callable, Iterator
from datetime import datetime
from pathlib import Path

from streamstats.errors import (
    StreamStatsError,
    UncorrectEventError,
    UncorrectFormatError,
    UncorrectTimeMark,
)
from streamstats.models import Event

InvalidLineHandler = Callable[[Path, int, str], None]
Parser = Callable[
    [Path, bool, InvalidLineHandler | None],
    Iterator[Event],
]
logger = logging.getLogger(__name__)

VALID_LEVELS = {
    "DEBUG",
    "INFO",
    "NOTICE",
    "WARNING",
    "ERROR",
    "CRITICAL",
}
REQUIRED_FIELDS = {"timestamp", "level", "source", "message"}


def _parse_event(data: object, path: Path, line_number: int) -> Event:
    """Проверяет данные и преобразует их в Event."""
    location = f"{path}:{line_number}"

    if not isinstance(data, dict):
        raise UncorrectEventError(
            f"{location}: ожидался JSON-объект"
        )

    missing = REQUIRED_FIELDS - data.keys()
    if missing:
        raise UncorrectEventError(
            f"{location}: отсутствуют поля: {', '.join(sorted(missing))}"
        )

    timestamp = data["timestamp"]
    level = data["level"]
    source = data["source"]
    message = data["message"]

    if not isinstance(timestamp, str):
        raise UncorrectTimeMark(
            f"{location}: timestamp должен быть строкой"
        )

    try:
        parsed_timestamp = datetime.fromisoformat(
            timestamp
        )
    except ValueError as exc:
        raise UncorrectTimeMark(
            f"{location}: некорректная временная метка {timestamp!r}"
        ) from exc

    if not isinstance(level, str) or level not in VALID_LEVELS:
        raise UncorrectEventError(
            f"{location}: недопустимый уровень события {level!r}"
        )

    if not isinstance(source, str) or not source.strip():
        raise UncorrectEventError(
            f"{location}: source должен быть непустой строкой"
        )

    if not isinstance(message, str):
        raise UncorrectEventError(
            f"{location}: message должен быть строкой"
        )

    return Event(
        timestamp=parsed_timestamp,
        level=level,
        source=source,
        message=message,
    )



def parse_jsonl(
    path: Path,
    skip_invalid: bool = False,
    on_invalid: InvalidLineHandler | None = None,
) -> Iterator[Event]:
    """Читает JSONL построчно, при необходимости пропуская ошибки."""
    try:
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                try:
                    data = json.loads(line)
                    yield _parse_event(data, path, line_number)

                except json.JSONDecodeError as exc:
                    error = UncorrectEventError(
                        f"{path}:{line_number}: некорректный JSON: {exc.msg}"
                    )
                    error.__cause__ = exc

                    if not skip_invalid:
                        raise error from exc

                    logger.warning("%s", error)
                    if on_invalid is not None:
                        on_invalid(path, line_number, str(error))

                except StreamStatsError as exc:
                    if not skip_invalid:
                        raise

                    logger.warning("%s", exc)
                    if on_invalid is not None:
                        on_invalid(path, line_number, str(exc))
    except UnicodeDecodeError as exc:
        raise UncorrectFormatError(
            f"Файл {path} не является корректным UTF-8"
        ) from exc





def parse_csv(
    path: Path,
    skip_invalid: bool = False,
    on_invalid: InvalidLineHandler | None = None,
) -> Iterator[Event]:
    """Читает CSV построчно, при необходимости пропуская ошибки."""
    with path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames is None:
            return

        missing = REQUIRED_FIELDS - set(reader.fieldnames)
        if missing:
            raise UncorrectFormatError(
                f"{path}: отсутствуют столбцы: "
                f"{', '.join(sorted(missing))}"
            )

        for line_number, row in enumerate(reader, start=2):
            try:
                if None in row:
                    raise UncorrectEventError(
                        f"{path}:{line_number}: лишние значения в строке CSV"
                    )

                yield _parse_event(row, path, line_number)

            except StreamStatsError as exc:
                if not skip_invalid:
                    raise

                logger.warning("%s", exc)
                if on_invalid is not None:
                    on_invalid(path, line_number, str(exc))

PARSERS: dict[str, Parser] = {
    "csv": parse_csv,
    "jsonl": parse_jsonl,
}


def register_parser(name: str, parser: Parser) -> None:
    """Регистрирует парсер нового формата."""
    if not name or not name.strip():
        raise ValueError("Название формата не может быть пустым")

    if name in PARSERS:
        raise ValueError(f"Парсер формата {name!r} уже зарегистрирован")

    PARSERS[name] = parser