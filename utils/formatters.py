"""Форматирование данных для отображения в дашборде."""

from config import MONTH_NAMES_RU


def format_number(value: float, decimals: int = 2) -> str:
    """Форматирование числа с разделителями тысяч (не более 2 знаков после запятой)."""
    decimals = min(max(decimals, 0), 2)
    rounded = round(float(value), decimals)

    if decimals == 0 or rounded == int(rounded):
        return f"{int(rounded):,}".replace(",", " ")

    formatted = f"{rounded:,.{decimals}f}"
    if "." in formatted:
        integer_part, fractional_part = formatted.rsplit(".", 1)
        return f"{integer_part.replace(',', ' ')},{fractional_part}"
    return formatted.replace(",", " ")


def format_currency(value: float, decimals: int = 2) -> str:
    """Форматирование суммы в рублях."""
    return f"{format_number(value, decimals)} ₽"


def format_percent(value: float, decimals: int = 2) -> str:
    """Форматирование процентов."""
    decimals = min(max(decimals, 0), 2)
    return f"{round(float(value), decimals):.{decimals}f}%"


def format_integer(value: int | float) -> str:
    """Форматирование целого числа с разделителями тысяч."""
    return f"{int(round(value)):,}".replace(",", " ")


def month_label(month_str: str) -> str:
    """Преобразование 'YYYY-MM' в читаемый формат с русским месяцем."""
    try:
        year, month = month_str.split("-")
        month_num = int(month)
        return f"{MONTH_NAMES_RU.get(month_num, month)} {year}"
    except (ValueError, AttributeError):
        return str(month_str)


def style_loss_ratio(val: float) -> str:
    """CSS-стиль для убыточности > 100%."""
    if val > 100:
        return "color: #d62728; font-weight: bold;"
    return ""
