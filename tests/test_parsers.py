import json
import logging

import pytest

from streamstats.errors import (
    UncorrectEventError,
    UncorrectTimeMark,
)
from streamstats.parsers import parse_csv, parse_jsonl

EVENTS = [
    {
        "timestamp": "2026-10-22T10:00:00",
        "level": "INFO",
        "source": "api",
        "message": "Сервис запущен",
    },
    {
        "timestamp": "2026-10-22T10:01:00",
        "level": "ERROR",
        "source": "база данных",
        "message": "Ошибка подключения",
    },
]


def write_jsonl(path, events):
    path.write_text(
        "".join(
            json.dumps(event, ensure_ascii=False) + "\n"
            for event in events
        ),
        encoding="utf-8",
    )
    return path


def write_csv(path, events):
    header = "timestamp,level,source,message\n"
    rows = [
        ",".join(
            f'"{event[field]}"'
            for field in ("timestamp", "level", "source", "message")
        )
        for event in events
    ]
    path.write_text(
        header + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    return path


def test_jsonl_parser_reads_events(tmp_path):
    path = write_jsonl(tmp_path / "events.jsonl", EVENTS)

    events = list(parse_jsonl(path))

    assert len(events) == 2
    assert events[0].level == "INFO"
    assert events[1].source == "база данных"
    assert events[1].message == "Ошибка подключения"


def test_csv_parser_reads_events(tmp_path):
    path = write_csv(tmp_path / "events.csv", EVENTS)

    events = list(parse_csv(path))

    assert len(events) == 2
    assert events[0].level == "INFO"
    assert events[1].source == "база данных"
    assert events[1].message == "Ошибка подключения"


def test_csv_and_jsonl_produce_equivalent_events(tmp_path):
    csv_path = write_csv(tmp_path / "events.csv", EVENTS)
    jsonl_path = write_jsonl(tmp_path / "events.jsonl", EVENTS)

    csv_events = list(parse_csv(csv_path))
    jsonl_events = list(parse_jsonl(jsonl_path))

    assert csv_events == jsonl_events


@pytest.mark.parametrize("parser, suffix", [
    (parse_csv, ".csv"),
    (parse_jsonl, ".jsonl"),
])
def test_empty_file_returns_no_events(tmp_path, parser, suffix):
    path = tmp_path / f"empty{suffix}"
    path.write_text("", encoding="utf-8")

    assert list(parser(path)) == []


def test_jsonl_invalid_line_raises_error_with_line_number(tmp_path):
    path = tmp_path / "broken.jsonl"
    path.write_text(
        '{"timestamp":"2026-10-22T10:00:00",'
        '"level":"INFO","source":"api","message":"OK"}\n'
        '{"timestamp":"2026-10-22T10:01:00",'
        '"level":"ERROR","source":\n',
        encoding="utf-8",
    )

    with pytest.raises(UncorrectEventError, match="2"):
        list(parse_jsonl(path))


def test_jsonl_invalid_timestamp_raises_error(tmp_path):
    path = tmp_path / "bad_timestamp.jsonl"
    path.write_text(
        '{"timestamp":"not-a-date","level":"INFO",'
        '"source":"api","message":"Ошибка даты"}\n',
        encoding="utf-8",
    )

    with pytest.raises(UncorrectTimeMark, match="1"):
        list(parse_jsonl(path))


def test_jsonl_skip_invalid_counts_skipped_lines(
    tmp_path, caplog
):
    path = tmp_path / "mixed.jsonl"
    path.write_text(
        '{"timestamp":"2026-10-22T10:00:00",'
        '"level":"INFO","source":"api","message":"Первое"}\n'
        '{"timestamp":"2026-10-22T10:01:00",'
        '"level":"ERROR","source":\n'
        '{"timestamp":"not-a-date","level":"INFO",'
        '"source":"api","message":"Плохая дата"}\n'
        '{"timestamp":"2026-10-22T10:03:00",'
        '"level":"INFO","source":"worker","message":"Последнее"}\n',
        encoding="utf-8",
    )

    skipped = []

    def on_invalid(path, line_number, message):
        skipped.append((line_number, message))

    with caplog.at_level(logging.WARNING):
        events = list(
            parse_jsonl(
                path,
                skip_invalid=True,
                on_invalid=on_invalid,
            )
        )

    assert len(events) == 2
    assert [line for line, _ in skipped] == [2, 3]
    assert len(skipped) == 2
    assert len(caplog.records) == 2


def test_csv_skip_invalid_counts_skipped_lines(tmp_path):
    path = tmp_path / "mixed.csv"
    path.write_text(
        "timestamp,level,source,message\n"
        "2026-10-22T10:00:00,INFO,api,Первое\n"
        "not-a-date,INFO,api,Плохая дата\n"
        "2026-10-22T10:02:00,ERROR,auth,Последнее\n",
        encoding="utf-8",
    )

    skipped = []

    events = list(
        parse_csv(
            path,
            skip_invalid=True,
            on_invalid=lambda p, n, m: skipped.append(n),
        )
    )

    assert len(events) == 2
    assert skipped == [3]
