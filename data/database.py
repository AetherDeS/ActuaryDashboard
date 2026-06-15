"""Работа с SQLite базой данных страховых договоров."""

import os
from typing import Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import DATABASE_PATH
from data.generator import DataGenerator
from utils.aggregations import aggregate_by_product, aggregate_by_region, aggregate_monthly


class Database:
    """Класс для управления SQLite базой данных."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self.engine: Optional[Engine] = None

    def _get_engine(self) -> Engine:
        if self.engine is None:
            self.engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        return self.engine

    # Порядок важен для FK: родительские таблицы создаются раньше дочерних.
    _TABLES = ["payouts", "contracts", "clients", "products", "regions"]

    _SCHEMA = [
        """
        CREATE TABLE IF NOT EXISTS regions (
            region_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS products (
            product_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL UNIQUE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS clients (
            client_id INTEGER PRIMARY KEY,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS contracts (
            contract_id TEXT PRIMARY KEY,
            region_id INTEGER NOT NULL REFERENCES regions(region_id),
            product_id INTEGER NOT NULL REFERENCES products(product_id),
            client_id INTEGER NOT NULL REFERENCES clients(client_id),
            premium REAL NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS payouts (
            payout_id INTEGER PRIMARY KEY,
            contract_id TEXT NOT NULL REFERENCES contracts(contract_id),
            payout_amount REAL NOT NULL,
            payout_date TEXT NOT NULL
        )
        """,
    ]

    def init_database(self) -> None:
        """Создание нормализованных таблиц (с миграцией со старой схемы)."""
        engine = self._get_engine()
        with engine.begin() as conn:
            # Миграция: удалить устаревшую денормализованную таблицу contracts.
            cols = [row[1] for row in conn.execute(text("PRAGMA table_info(contracts)"))]
            if cols and "region_id" not in cols:
                conn.execute(text("DROP TABLE IF EXISTS contracts"))
            for ddl in self._SCHEMA:
                conn.execute(text(ddl))

    def insert_data(self, df: pd.DataFrame) -> None:
        """Разложить плоский DataFrame по нормализованным таблицам."""
        engine = self._get_engine()

        # Чистый перезалив: убрать старые таблицы и создать схему заново.
        with engine.begin() as conn:
            for table in self._TABLES:
                conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        self.init_database()

        data = df.copy()
        data["start_date"] = pd.to_datetime(data["start_date"])
        data["end_date"] = pd.to_datetime(data["end_date"])

        regions = pd.DataFrame({"name": sorted(data["region"].unique())})
        regions.insert(0, "region_id", range(1, len(regions) + 1))
        products = pd.DataFrame({"name": sorted(data["product"].unique())})
        products.insert(0, "product_id", range(1, len(products) + 1))

        region_map = dict(zip(regions["name"], regions["region_id"]))
        product_map = dict(zip(products["name"], products["product_id"]))

        # Один клиент на договор (в MVP клиент не переиспользуется).
        clients = pd.DataFrame({
            "client_id": range(1, len(data) + 1),
            "age": data["client_age"].to_numpy(),
            "gender": data["client_gender"].to_numpy(),
        })

        contracts = pd.DataFrame({
            "contract_id": data["contract_id"].to_numpy(),
            "region_id": data["region"].map(region_map).to_numpy(),
            "product_id": data["product"].map(product_map).to_numpy(),
            "client_id": clients["client_id"].to_numpy(),
            "premium": data["premium"].to_numpy(),
            "start_date": data["start_date"].dt.strftime("%Y-%m-%d").to_numpy(),
            "end_date": data["end_date"].dt.strftime("%Y-%m-%d").to_numpy(),
        })

        # Выплата создаётся только при наступлении страхового случая (payout > 0).
        claims = data[data["payout"] > 0].copy()
        claim_dates = claims["start_date"] + (claims["end_date"] - claims["start_date"]) / 2
        payouts = pd.DataFrame({
            "payout_id": range(1, len(claims) + 1),
            "contract_id": claims["contract_id"].to_numpy(),
            "payout_amount": claims["payout"].to_numpy(),
            "payout_date": claim_dates.dt.strftime("%Y-%m-%d").to_numpy(),
        })

        regions.to_sql("regions", engine, if_exists="append", index=False)
        products.to_sql("products", engine, if_exists="append", index=False)
        clients.to_sql("clients", engine, if_exists="append", index=False)
        contracts.to_sql("contracts", engine, if_exists="append", index=False)
        payouts.to_sql("payouts", engine, if_exists="append", index=False)

    def get_contracts(self, filters: Optional[dict[str, Any]] = None) -> pd.DataFrame:
        """Плоское представление договоров (JOIN + суммарная выплата) с фильтрами."""
        filters = filters or {}
        query = """
            SELECT c.contract_id,
                   r.name AS region,
                   p.name AS product,
                   c.premium,
                   COALESCE(pay.payout, 0) AS payout,
                   c.start_date,
                   c.end_date,
                   cl.age AS client_age,
                   cl.gender AS client_gender
            FROM contracts c
            JOIN regions r ON r.region_id = c.region_id
            JOIN products p ON p.product_id = c.product_id
            JOIN clients cl ON cl.client_id = c.client_id
            LEFT JOIN (
                SELECT contract_id, SUM(payout_amount) AS payout
                FROM payouts
                GROUP BY contract_id
            ) pay ON pay.contract_id = c.contract_id
            WHERE 1=1
        """
        params: dict[str, Any] = {}

        if filters.get("start_date"):
            query += " AND c.start_date >= :start_date"
            params["start_date"] = str(filters["start_date"])

        if filters.get("end_date"):
            query += " AND c.start_date <= :end_date"
            params["end_date"] = str(filters["end_date"])

        if filters.get("regions"):
            placeholders = ", ".join(f":region_{i}" for i in range(len(filters["regions"])))
            query += f" AND r.name IN ({placeholders})"
            for i, region in enumerate(filters["regions"]):
                params[f"region_{i}"] = region

        if filters.get("products"):
            placeholders = ", ".join(f":product_{i}" for i in range(len(filters["products"])))
            query += f" AND p.name IN ({placeholders})"
            for i, product in enumerate(filters["products"]):
                params[f"product_{i}"] = product

        try:
            engine = self._get_engine()
            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
            if not df.empty:
                df["start_date"] = pd.to_datetime(df["start_date"])
                df["end_date"] = pd.to_datetime(df["end_date"])
            return df
        except Exception as e:
            raise RuntimeError(f"Ошибка получения договоров: {e}") from e

    def get_monthly_stats(self, filters: Optional[dict[str, Any]] = None) -> pd.DataFrame:
        """Агрегированные данные по месяцам."""
        return aggregate_monthly(self.get_contracts(filters))

    def get_region_stats(self, filters: Optional[dict[str, Any]] = None) -> pd.DataFrame:
        """Статистика по регионам."""
        return aggregate_by_region(self.get_contracts(filters))

    def get_product_stats(self, filters: Optional[dict[str, Any]] = None) -> pd.DataFrame:
        """Статистика по продуктам."""
        return aggregate_by_product(self.get_contracts(filters))

    def close(self) -> None:
        """Закрытие соединения с БД."""
        if self.engine is not None:
            self.engine.dispose()
            self.engine = None


def ensure_data_loaded(db_path: str = DATABASE_PATH) -> Database:
    """Инициализация БД и загрузка тестовых данных при первом запуске."""
    db = Database(db_path)
    db.init_database()

    if not os.path.exists(db_path) or _is_database_empty(db):
        with st_spinner_safe("Генерация тестовых данных..."):
            generator = DataGenerator(n_contracts=10000)
            df = generator.generate()
            db.insert_data(df)

    return db


def _is_database_empty(db: Database) -> bool:
    """Проверка, пуста ли таблица contracts."""
    try:
        engine = db._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM contracts")).scalar()
        return result == 0
    except Exception:
        return True


def st_spinner_safe(message: str):
    """Контекстный менеджер-заглушка для использования вне Streamlit."""
    import contextlib

    @contextlib.contextmanager
    def _dummy():
        yield

    try:
        import streamlit as st
        return st.spinner(message)
    except Exception:
        return _dummy()
