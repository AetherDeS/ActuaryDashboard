"""Тесты актуарных расчётов (utils/calculations.py)."""

import pandas as pd
import pytest

from utils.calculations import (
    add_trend_line,
    calculate_frequency,
    calculate_loss_ratio,
    calculate_period_delta,
    calculate_reserve,
    calculate_severity,
    forecast_next_period,
)


class TestLossRatio:
    def test_normal(self):
        assert calculate_loss_ratio(1000, 500) == 50.0

    def test_zero_premium_returns_zero(self):
        assert calculate_loss_ratio(0, 100) == 0.0

    def test_above_hundred(self):
        assert calculate_loss_ratio(1000, 1500) == 150.0


class TestFrequency:
    def test_normal(self):
        assert calculate_frequency(100, 30) == 30.0

    def test_zero_policies_returns_zero(self):
        assert calculate_frequency(0, 5) == 0.0


class TestSeverity:
    def test_normal(self):
        assert calculate_severity(1000, 4) == 250.0

    def test_zero_claims_returns_zero(self):
        assert calculate_severity(1000, 0) == 0.0


class TestReserve:
    def test_below_target_is_ten_percent(self):
        assert calculate_reserve(1000, 50) == 100.0

    def test_at_target_boundary(self):
        assert calculate_reserve(1000, 70) == 100.0

    def test_above_target_proportional(self):
        # excess = (90 - 70) / 100 = 0.2
        assert calculate_reserve(1000, 90) == pytest.approx(200.0)


class TestPeriodDelta:
    def test_increase(self):
        assert calculate_period_delta(110, 100) == pytest.approx(10.0)

    def test_decrease(self):
        assert calculate_period_delta(90, 100) == pytest.approx(-10.0)

    def test_zero_previous_zero_current(self):
        assert calculate_period_delta(0, 0) == 0.0

    def test_zero_previous_nonzero_current(self):
        assert calculate_period_delta(5, 0) == 100.0


class TestForecast:
    def test_empty_input(self):
        result = forecast_next_period(pd.DataFrame(), "total_premium", periods=3)
        assert result.empty
        assert list(result.columns) == ["period", "forecast", "type"]

    def test_missing_column(self):
        df = pd.DataFrame({"other": [1, 2, 3]})
        result = forecast_next_period(df, "total_premium", periods=3)
        assert result.empty

    def test_moving_average_when_few_points(self):
        df = pd.DataFrame({"total_premium": [100.0, 200.0]})
        result = forecast_next_period(df, "total_premium", periods=3)
        assert len(result) == 3
        assert (result["type"] == "moving_average").all()
        assert result["forecast"].tolist() == [150.0, 150.0, 150.0]

    def test_linear_regression_on_trend(self):
        df = pd.DataFrame({"total_premium": [10.0, 20.0, 30.0, 40.0]})
        result = forecast_next_period(df, "total_premium", periods=3)
        assert len(result) == 3
        assert (result["type"] == "linear_regression").all()
        assert result["forecast"].tolist() == pytest.approx([50.0, 60.0, 70.0])


class TestTrendLine:
    def test_too_few_points_returns_input(self):
        x, y = add_trend_line([0], [5])
        assert x == [0]
        assert y == [5]

    def test_linear_series_trend_matches(self):
        _, trend = add_trend_line([0, 1, 2, 3], [10, 20, 30, 40])
        assert trend == pytest.approx([10.0, 20.0, 30.0, 40.0])
