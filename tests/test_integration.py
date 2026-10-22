import json

from streamstats.__main__ import main


def test_multiple_jsonl_files_are_aggregated(tmp_path):
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    output = tmp_path / "report.json"

    first.write_text(
        '{"timestamp":"2026-10-22T10:00:00","level":"INFO",'
        '"source":"api","message":"Первое"}\n',
        encoding="utf-8",
    )
    second.write_text(
        '{"timestamp":"2026-10-22T10:01:00","level":"ERROR",'
        '"source":"database","message":"Второе"}\n',
        encoding="utf-8",
    )

    original_first = first.read_bytes()
    original_second = second.read_bytes()

    exit_code = main([
        "analyze",
        str(first),
        str(second),
        "--format", "jsonl",
        "--output", str(output),
    ])

    report = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["total_events"] == 2
    assert report["by_level"]["INFO"] == 1
    assert report["by_level"]["ERROR"] == 1
    assert report["by_source"] == {"api": 1, "database": 1}
    assert report["skipped_lines"] == 0
    assert first.read_bytes() == original_first
    assert second.read_bytes() == original_second


def test_cli_skip_invalid_integration(tmp_path):
    source = tmp_path / "events.jsonl"
    output = tmp_path / "report.json"

    source.write_text(
        '{"timestamp":"2026-10-22T10:00:00","level":"INFO",'
        '"source":"api","message":"Нормальное событие"}\n'
        '{"timestamp":"2026-10-22T10:01:00","level":"ERROR",'
        '"source":\n'
        '{"timestamp":"2026-10-22T10:02:00","level":"INFO",'
        '"source":"worker","message":"Ещё событие"}\n',
        encoding="utf-8",
    )

    exit_code = main([
        "analyze",
        str(source),
        "--format", "jsonl",
        "--output", str(output),
        "--skip-invalid",
    ])

    report = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert report["total_events"] == 2
    assert report["skipped_lines"] == 1


def test_cli_without_skip_invalid_returns_error(tmp_path, capsys):
    source = tmp_path / "broken.jsonl"

    source.write_text(
        '{"timestamp":"2026-10-22T10:00:00","level":"INFO",'
        '"source":\n',
        encoding="utf-8",
    )

    exit_code = main([
        "analyze",
        str(source),
        "--format", "jsonl",
    ])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Ошибка" in captured.err
    assert str(source) in captured.err
