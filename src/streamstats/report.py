import csv
import json
import sys
from pathlib import Path
from typing import TextIO


def write_report(
    report: dict,
    output: Path | None = None,
) -> None:
    """Записывает JSON-отчёт в файл или стандартный вывод."""
    if output is None:
        stream: TextIO = sys.stdout
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        return

    with output.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write("\n")


def write_csv_report(
    report: dict,
    output: Path | None = None,
) -> None:
    """Записывает готовую статистику в CSV без повторного анализа."""
    if output is None:
        stream: TextIO = sys.stdout
        close_stream = False
    else:
        stream = output.open("w", encoding="utf-8", newline="")
        close_stream = True

    try:
        writer = csv.writer(stream)
        writer.writerow(["metric", "value"])

        writer.writerow(["total_events", report["total_events"]])
        writer.writerow(["skipped_lines", report["skipped_lines"]])

        for level, count in report["by_level"].items():
            writer.writerow([f"level.{level}", count])

        for source, count in report["by_source"].items():
            writer.writerow([f"source.{source}", count])

        writer.writerow(["min_timestamp", report["min_timestamp"] or ""])
        writer.writerow(["max_timestamp", report["max_timestamp"] or ""])

        for item in report["top_error_sources"]:
            writer.writerow([
                f"top_error_source.{item['source']}",
                item["count"],
            ])
    finally:
        if close_stream:
            stream.close()
