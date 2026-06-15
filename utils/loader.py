"""Загрузка данных и общие фильтры для всех страниц."""

from datetime import date, timedelta
from typing import Any

import pandas as pd
import streamlit as st

from config import DEFAULT_FILTER_YEARS, ORACLE_CONFIG, PRODUCTS, REGIONS
from data.database import Database, ensure_data_loaded
from data.oracle_connector import OracleConnector


def _default_start_date() -> date:
    """Начало периода по умолчанию: 1 января N лет назад от текущего года."""
    return date(date.today().year - DEFAULT_FILTER_YEARS, 1, 1)


def init_session_state() -> None:
    """Инициализация фильтров в session_state."""
    defaults = {
        "start_date": _default_start_date(),
        "end_date": date.today(),
        "regions": REGIONS.copy(),
        "products": PRODUCTS.copy(),
        "use_oracle": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


@st.cache_resource
def get_database() -> Database:
    """Кэшированное подключение к SQLite."""
    return ensure_data_loaded()


@st.cache_data(ttl=300)
def load_contracts_cached(
    start_date: str,
    end_date: str,
    regions: tuple,
    products: tuple,
    use_oracle: bool,
) -> pd.DataFrame:
    """Кэшированная загрузка договоров с учётом фильтров."""
    filters = {
        "start_date": start_date,
        "end_date": end_date,
        "regions": list(regions),
        "products": list(products),
    }

    if use_oracle:
        connector = OracleConnector()
        df = connector.get_sample_contracts(start_date, end_date)
        connector.close()
        if not df.empty:
            if regions:
                df = df[df["region"].isin(regions)]
            if products:
                df = df[df["product"].isin(products)]
        return df

    db = get_database()
    return db.get_contracts(filters)


def get_filters() -> dict[str, Any]:
    """Текущие значения фильтров из session_state."""
    return {
        "start_date": st.session_state.start_date,
        "end_date": st.session_state.end_date,
        "regions": st.session_state.regions,
        "products": st.session_state.products,
        "use_oracle": st.session_state.use_oracle,
    }


def load_filtered_data() -> pd.DataFrame:
    """Загрузить отфильтрованные данные."""
    f = get_filters()
    try:
        return load_contracts_cached(
            str(f["start_date"]),
            str(f["end_date"]),
            tuple(f["regions"]),
            tuple(f["products"]),
            f["use_oracle"],
        )
    except Exception as e:
        if f["use_oracle"]:
            st.error(
                "**Ошибка подключения к Oracle DB.**\n\n"
                "Для работы с Oracle необходимо:\n"
                "1. Установить драйвер: `pip install oracledb`\n"
                "2. Настроить параметры `ORACLE_CONFIG` в файле `config.py`\n\n"
                f"*(Техническая информация: {e})*"
            )
            st.info("Временно используются локальные тестовые данные (SQLite).")
            return load_contracts_cached(
                str(f["start_date"]),
                str(f["end_date"]),
                tuple(f["regions"]),
                tuple(f["products"]),
                False,
            )
        raise e


def _reset_filters() -> None:
    """Сброс фильтров к значениям по умолчанию."""
    st.session_state.start_date = _default_start_date()
    st.session_state.end_date = date.today()
    st.session_state.regions = REGIONS.copy()
    st.session_state.products = PRODUCTS.copy()
    st.session_state.use_oracle = False


def render_sidebar() -> None:
    """Боковая панель с фильтрами (общая для всех страниц)."""
    from utils.ui import render_navigation

    init_session_state()
    render_navigation()

    with st.sidebar:
        with st.expander("Фильтры", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.date_input("Дата от", key="start_date")
            with col2:
                st.date_input("Дата до", key="end_date")

            if st.session_state.start_date > st.session_state.end_date:
                st.warning("Дата начала позже даты окончания. Проверьте период.")

            st.multiselect("Регионы", options=REGIONS, key="regions")
            st.multiselect("Продукты", options=PRODUCTS, key="products")
            
            period_days = (st.session_state.end_date - st.session_state.start_date).days
            st.caption(f"Выбранный период: {period_days} дн.")

        st.checkbox(
            "Использовать Oracle",
            key="use_oracle",
        )

        if st.session_state.use_oracle:
            st.info("Режим Oracle: требуется настройка ORACLE_CONFIG.")
            with st.expander("Конфигурация подключения Oracle"):
                safe_config = {
                    **ORACLE_CONFIG,
                    "password": "***" if ORACLE_CONFIG.get("password") else "(не задан)",
                }
                st.code(str(safe_config), language="python")


def validate_filters() -> bool:
    """Проверка корректности фильтров."""
    if not st.session_state.regions:
        st.warning("Выберите хотя бы один регион.")
        return False
    if not st.session_state.products:
        st.warning("Выберите хотя бы один продукт.")
        return False
    if st.session_state.start_date > st.session_state.end_date:
        st.warning("Некорректный период: дата начала позже даты окончания.")
        return False
    return True


def get_previous_period_data(df: pd.DataFrame) -> pd.DataFrame:
    """Данные за предыдущий период той же длительности."""
    if df.empty:
        return df

    start = pd.to_datetime(st.session_state.start_date)
    end = pd.to_datetime(st.session_state.end_date)
    period_len = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=period_len - 1)

    f = get_filters()
    return load_contracts_cached(
        str(prev_start.date()),
        str(prev_end.date()),
        tuple(f["regions"]),
        tuple(f["products"]),
        f["use_oracle"],
    )
