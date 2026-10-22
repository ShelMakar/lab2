import csv

from streamstats.report import write_csv_report


def test_write_csv_report(tmp_path):
    output = tmp_path / "report.csv"

    report = {
        "total_events": 2,
        "skipped_lines": 1,
        "by_level": {
            "DEBUG": 0,
            "INFO": 1,
            "WARNING": 0,
            "ERROR": 1,
            "CRITICAL": 0,
        },
        "by_source": {"api": 1, "база данных": 1},
        "top_error_sources": [
            {"source": "база данных", "count": 1},
        ],
        "min_timestamp": "2026-10-22T10:00:00",
        "max_timestamp": "2026-10-22T11:00:00",
    }

    write_csv_report(report, output)

    with output.open(encoding="utf-8", newline="") as file:
        rows = list(csv.reader(file))

    assert rows[0] == ["metric", "value"]
    assert ["total_events", "2"] in rows
    assert ["skipped_lines", "1"] in rows
    assert ["level.INFO", "1"] in rows
    assert ["source.база данных", "1"] in rows
    assert ["top_error_source.база данных", "1"] in rows
