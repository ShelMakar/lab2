from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime

from streamstats.models import Event

LEVELS = (
    "DEBUG",
    "INFO",
    "NOTICE",
    "WARNING",
    "ERROR",
    "CRITICAL",
)

def analyze_events(
    events: Iterable[Event],
    skipped_lines: int = 0,
) -> dict:
    """Собирает статистику по потоку событий."""
    total_events = 0
    level_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    error_source_counts: Counter[str] = Counter()

    min_timestamp: datetime | None = None
    max_timestamp: datetime | None = None

    for event in events:
        total_events += 1
        level_counts[event.level] += 1
        source_counts[event.source] += 1

        timestamp = event.timestamp

        # Приводим время к UTC для корректного сравнения.
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        else:
            timestamp = timestamp.astimezone(UTC)

        if min_timestamp is None or timestamp < min_timestamp:
            min_timestamp = timestamp

        if max_timestamp is None or timestamp > max_timestamp:
            max_timestamp = timestamp


    top_error_sources = [
        {"source": source, "count": count}
        for source, count in sorted(
            error_source_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[:5]
    ]

    return {
        "total_events": total_events,
        "by_level": {
            level: level_counts.get(level, 0)
            for level in LEVELS
        },
        "by_source": dict(sorted(source_counts.items())),
        "top_error_sources": top_error_sources,
        "min_timestamp": (
            min_timestamp.isoformat() if min_timestamp is not None else None
        ),
        "max_timestamp": (
            max_timestamp.isoformat() if max_timestamp is not None else None
        ),
        "skipped_lines": skipped_lines,
    }
