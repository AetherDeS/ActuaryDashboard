"""Тесты форматирования (utils/formatters.py)."""

from utils.formatters import (
    format_currency,
    format_integer,
    format_number,
    format_percent,
    month_label,
    style_loss_ratio,
)


class TestFormatNumber:
    def test_thousands_separator_is_space(self):
        assert format_number(1234567) == "1 234 567"

    def test_integer_value_no_decimals(self):
        assert format_number(1000.0) == "1 000"

    def test_decimal_uses_comma(self):
        assert format_number(1234.5, 2) == "1 234,50"

    def test_decimals_clamped_to_two(self):
        assert format_number(1.23456, 5) == "1,23"


class TestFormatCurrency:
    def test_appends_ruble_sign(self):
        assert format_currency(1000) == "1 000 ₽"


class TestFormatPercent:
    def test_basic(self):
        assert format_percent(12.5) == "12.50%"

    def test_no_thousands_separator(self):
        # Защита от регрессии: проценты не содержат пробелов-разделителей.
        out = format_percent(1234.56)
        assert " " not in out
        assert out == "1234.56%"


class TestFormatInteger:
    def test_rounds_and_separates(self):
        assert format_integer(1234.6) == "1 235"


class TestMonthLabel:
    def test_valid(self):
        assert month_label("2022-03") == "Мар 2022"

    def test_invalid_returns_input(self):
        assert month_label("not-a-month") == "not-a-month"


class TestStyleLossRatio:
    def test_high_is_highlighted(self):
        assert "color" in style_loss_ratio(120)

    def test_normal_is_empty(self):
        assert style_loss_ratio(50) == ""
