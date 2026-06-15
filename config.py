"""Конфигурация актуарного дашборда."""

import os

DATABASE_PATH = "actuary_data.db"

# Глубина периода фильтра по умолчанию: сколько лет истории показывать
# (начало периода = 1 января N лет назад от текущего года).
DEFAULT_FILTER_YEARS = 3

ORACLE_CONFIG = {
    "user": os.getenv("ORACLE_USER", "actuary_user"),
    "password": os.getenv("ORACLE_PASSWORD", ""),
    "dsn": os.getenv("ORACLE_DSN", "localhost:1521/ORCL"),
    "encoding": os.getenv("ORACLE_ENCODING", "UTF-8"),
}

REGIONS = [
    "Москва",
    "СПб",
    "Казань",
    "Екатеринбург",
    "Новосибирск",
    "Краснодар",
    "Нижний Новгород",
    "Ростов-на-Дону",
    "Уфа",
    "Самара",
]

PRODUCTS = [
    "ОСАГО",
    "КАСКО",
    "Страхование имущества",
    "Ипотека",
    "ДМС",
    "НС",
]

COLORS = {
    "blue": "#1f77b4",
    "orange": "#ff7f0e",
    "green": "#2ca02c",
    "red": "#d62728",
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
}

PLOTLY_TEMPLATE = {
    "layout": {
        "font": {"family": "Arial, sans-serif"},
        "colorway": ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"],
    }
}

MONTH_NAMES_RU = {
    1: "Янв", 2: "Фев", 3: "Мар", 4: "Апр", 5: "Май", 6: "Июн",
    7: "Июл", 8: "Авг", 9: "Сен", 10: "Окт", 11: "Ноя", 12: "Дек",
}
