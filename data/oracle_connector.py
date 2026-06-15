"""Подключение к Oracle DB (заглушка для production-интеграции)."""

from typing import Any, Optional

import pandas as pd

from config import ORACLE_CONFIG

# Пример SQL запроса для получения данных о договорах с JOIN таблиц выплат
SAMPLE_CONTRACTS_QUERY = """
SELECT c.contract_id, c.region, c.product, c.premium,
       COALESCE(SUM(v.payout_amount), 0) as payout,
       c.start_date, c.end_date, c.client_age, c.client_gender
FROM contracts c
LEFT JOIN payouts v ON c.contract_id = v.contract_id
WHERE c.start_date BETWEEN TO_DATE(:start_date, 'YYYY-MM-DD') AND TO_DATE(:end_date, 'YYYY-MM-DD')
GROUP BY c.contract_id, c.region, c.product, c.premium, c.start_date, c.end_date, c.client_age, c.client_gender
"""

SAMPLE_MONTHLY_QUERY = """
SELECT TO_CHAR(start_date, 'YYYY-MM') as month,
       SUM(premium) as total_premium,
       SUM(COALESCE(payout, 0)) as total_payout,
       COUNT(*) as contract_count
FROM contracts
GROUP BY TO_CHAR(start_date, 'YYYY-MM')
ORDER BY month
"""


class OracleConnector:
    """Класс для подключения к Oracle и выполнения SQL-запросов."""

    def __init__(self, config: Optional[dict[str, Any]] = None):
        self.config = config or ORACLE_CONFIG
        self.connection = None
        self._results: Optional[list] = None
        self._columns: list[str] = []

    def connect(self) -> bool:
        """Подключение к Oracle (используя oracledb)."""
        try:
            import oracledb

            self.connection = oracledb.connect(
                user=self.config["user"],
                password=self.config["password"],
                dsn=self.config["dsn"],
            )
            return True
        except Exception as e:
            raise ConnectionError(
                f"Не удалось подключиться к Oracle: {e}. "
                "Проверьте ORACLE_CONFIG в config.py и доступность сервера."
            ) from e

    def execute_query(self, query: str, params: Optional[dict[str, Any]] = None) -> None:
        """Выполнение SQL запроса."""
        if self.connection is None:
            self.connect()

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or {})
            self._columns = [col[0] for col in cursor.description] if cursor.description else []
            self._results = cursor.fetchall()
            cursor.close()
        except Exception as e:
            raise RuntimeError(f"Ошибка выполнения запроса Oracle: {e}") from e

    def fetch_all(self) -> list:
        """Получение всех результатов последнего запроса."""
        if self._results is None:
            return []
        return self._results

    def fetch_dataframe(self, query: str, params: Optional[dict[str, Any]] = None) -> pd.DataFrame:
        """Выполнить запрос и вернуть результат как DataFrame."""
        self.execute_query(query, params)
        if self.connection is None or self._results is None:
            return pd.DataFrame()

        return pd.DataFrame(self._results, columns=self._columns)

    def close(self) -> None:
        """Закрытие соединения с Oracle."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def get_sample_contracts(
        self, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """Пример получения договоров с выплатами через JOIN."""
        return self.fetch_dataframe(
            SAMPLE_CONTRACTS_QUERY,
            {"start_date": start_date, "end_date": end_date},
        )
