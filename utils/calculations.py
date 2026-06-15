"""Актуарные расчёты для страховой аналитики."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def calculate_loss_ratio(premium: float, payout: float) -> float:
    """Коэффициент убыточности (в процентах)."""
    if premium == 0:
        return 0.0
    return (payout / premium) * 100


def calculate_frequency(policies: int, claims: int) -> float:
    """Частота страховых случаев (в процентах)."""
    if policies == 0:
        return 0.0
    return (claims / policies) * 100


def calculate_severity(payout: float, claims: int) -> float:
    """Тяжесть убытков (средняя выплата на один страховой случай)."""
    if claims == 0:
        return 0.0
    return payout / claims


def calculate_reserve(premium: float, loss_ratio: float) -> float:
    """Расчёт резервов на основе премии и коэффициента убыточности."""
    target_ratio = 70.0  # целевой коэффициент убыточности
    if loss_ratio <= target_ratio:
        return premium * 0.1
    excess = (loss_ratio - target_ratio) / 100
    return premium * excess


def forecast_next_period(
    data: pd.DataFrame,
    value_col: str = "total_premium",
    periods: int = 12,
) -> pd.DataFrame:
    """
    Прогноз на следующий период.
    Использует линейную регрессию, при недостатке данных — скользящее среднее.
    """
    if data.empty or value_col not in data.columns:
        return pd.DataFrame(columns=["period", "forecast", "type"])

    values = data[value_col].values
    n = len(values)

    if n < 3:
        avg = np.mean(values) if n > 0 else 0
        forecast_values = [avg] * periods
        method = "moving_average"
    else:
        x = np.arange(n).reshape(-1, 1)
        y = values
        model = LinearRegression()
        model.fit(x, y)
        future_x = np.arange(n, n + periods).reshape(-1, 1)
        forecast_values = model.predict(future_x)
        method = "linear_regression"

    last_period = data.index[-1] if hasattr(data.index[-1], "__str__") else n - 1
    periods_list = list(range(1, periods + 1))

    return pd.DataFrame({
        "period": [f"Прогноз +{p}" for p in periods_list],
        "forecast": forecast_values,
        "type": method,
        "base_period": str(last_period),
    })


def calculate_period_delta(current: float, previous: float) -> float:
    """Изменение метрики относительно предыдущего периода (%)."""
    if previous == 0:
        return 0.0 if current == 0 else 100.0
    return ((current - previous) / previous) * 100


def add_trend_line(x_values: list, y_values: list) -> tuple[list, list]:
    """Добавить линию тренда для графика."""
    if len(x_values) < 2:
        return x_values, y_values

    x_numeric = np.arange(len(x_values))
    coeffs = np.polyfit(x_numeric, y_values, 1)
    trend = np.polyval(coeffs, x_numeric)
    return list(x_values), list(trend)
