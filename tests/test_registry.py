import pytest

from streamstats.parsers import PARSERS, parse_csv, parse_jsonl, register_parser


def test_builtin_parsers_registered():
    assert PARSERS["csv"] is parse_csv
    assert PARSERS["jsonl"] is parse_jsonl


def test_register_parser():
    def custom_parser(path, skip_invalid=False, on_invalid=None):
        return iter(())

    register_parser("custom-test", custom_parser)

    assert PARSERS["custom-test"] is custom_parser


def test_register_duplicate_parser():
    def custom_parser(path, skip_invalid=False, on_invalid=None):
        return iter(())

    with pytest.raises(ValueError, match="уже зарегистрирован"):
        register_parser("csv", custom_parser)