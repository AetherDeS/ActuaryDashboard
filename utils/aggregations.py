"""Чистые агрегации поверх загруженного DataFrame.

Единый источник формул для страниц и слоя данных (`data/database.py`).
Функции не обращаются к БД и не зависят от Streamlit — на вход принимают
готовый DataFrame договоров.
"""

import pandas as pd

MONTHLY_COLUMNS = ["month", "total_premium", "total_payout", "contract_count", "loss_ratio"]
GROUP_COLUMNS = ["total_premium", "total_payout", "contract_count", "claims_count", "loss_ratio"]


def loss_ratio_series(premium: pd.Series, payout: pd.Series) -> pd.Series:
    """Векторизованный коэффициент убыточности (%) с защитой от деления на ноль."""
    ratio = pd.Series(0.0, index=premium.index)
    mask = premium != 0
    ratio[mask] = payout[mask] / premium[mask] * 100
    return ratio


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Агрегация премий, выплат и числа договоров по месяцам начала договора."""
    if df.empty:
        return pd.DataFrame(columns=MONTHLY_COLUMNS)

    out = df.copy()
    out["month"] = out["start_date"].dt.to_period("M").astype(str)
    stats = out.groupby("month").agg(
        total_premium=("premium", "sum"),
        total_payout=("payout", "sum"),
        contract_count=("contract_id", "count"),
    ).reset_index()
    stats["loss_ratio"] = loss_ratio_series(stats["total_premium"], stats["total_payout"])
    return stats.sort_values("month").reset_index(drop=True)


def aggregate_by(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    """Агрегация по произвольной категории (`region`, `product`) с loss ratio."""
    if df.empty:
        return pd.DataFrame(columns=[group_col, *GROUP_COLUMNS])

    stats = df.groupby(group_col).agg(
        total_premium=("premium", "sum"),
        total_payout=("payout", "sum"),
        contract_count=("contract_id", "count"),
        claims_count=("payout", lambda x: (x > 0).sum()),
    ).reset_index()
    stats["loss_ratio"] = loss_ratio_series(stats["total_premium"], stats["total_payout"])
    return stats.sort_values("total_premium", ascending=False).reset_index(drop=True)


def aggregate_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Статистика по регионам."""
    return aggregate_by(df, "region")


def aggregate_by_product(df: pd.DataFrame) -> pd.DataFrame:
    """Статистика по продуктам."""
    return aggregate_by(df, "product")
