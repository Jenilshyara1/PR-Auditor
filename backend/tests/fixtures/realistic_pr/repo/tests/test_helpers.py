from src.utils.helpers import format_currency


def test_format_currency() -> None:
    assert format_currency(5) == "$5"
