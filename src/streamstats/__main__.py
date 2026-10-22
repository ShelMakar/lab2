import argparse
import logging
import sys
from collections.abc import Iterator
from pathlib import Path

from streamstats.analysis import analyze_events
from streamstats.errors import StreamStatsError
from streamstats.models import Event
from streamstats.parsers import PARSERS
from streamstats.report import write_csv_report, write_report


def build_parser() -> argparse.ArgumentParser:
    """Создаёт и настраивает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        prog="streamstats",
        description="Потоковый анализатор файлов событий",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Проанализировать файлы событий",
    )
    analyze_parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="Пути к входным файлам",
    )
    analyze_parser.add_argument(
        "--format",
        required=True,
        choices=tuple(PARSERS),
        help="Формат входных файлов",
    )
    analyze_parser.add_argument(
        "--output",
        type=Path,
        help="Путь для сохранения JSON-отчёта",
    )
    analyze_parser.add_argument(
        "--report-format",
        choices=("json", "csv"),
        default="json",
        help="Формат выходного отчёта",
    )
    analyze_parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Пропускать некорректные строки",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Точка входа приложения."""
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command != "analyze":
        parser.error("неизвестная команда")

    skipped_count = 0

    def count_invalid(
        path: Path,
        line_number: int,
        message: str,
    ) -> None:
        nonlocal skipped_count
        skipped_count += 1

    def read_events() -> Iterator[Event]:
        parser_func = PARSERS[args.format]

        for input_path in args.inputs:
            events = parser_func(
                input_path,
                args.skip_invalid,
                count_invalid,
            )
            yield from events
    try:
        report_data = analyze_events(read_events())
        report_data["skipped_lines"] = skipped_count
        if args.report_format == "csv":
            write_csv_report(report_data, args.output)
        else:
            write_report(report_data, args.output)

    except (StreamStatsError, OSError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
