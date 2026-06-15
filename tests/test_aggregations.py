"""Тесты чистых агрегаций (utils/aggregations.py)."""

import pandas as pd
import pytest

from utils.aggregations import (
    aggregate_by_product,
    aggregate_by_region,
    aggregate_monthly,
    loss_ratio_series,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "contract_id": ["A", "B", "C", "D"],
        "region": ["Москва", "Москва", "СПб", "СПб"],
        "product": ["ОСАГО", "КАСКО", "ОСАГО", "ОСАГО"],
        "premium": [100.0, 200.0, 300.0, 400.0],
        "payout": [50.0, 0.0, 600.0, 0.0],
        "start_date": pd.to_datetime(
            ["2023-01-10", "2023-01-20", "2023-02-05", "2023-02-15"]
        ),
    })


class TestLossRatioSeries:
    def test_formula_and_zero_protection(self):
        premium = pd.Series([100.0, 0.0, 200.0])
        payout = pd.Series([50.0, 999.0, 400.0])
        result = loss_ratio_series(premium, payout)
        assert result.tolist() == [50.0, 0.0, 200.0]


class TestAggregateMonthly:
    def test_empty(self):
        result = aggregate_monthly(pd.DataFrame())
        assert result.empty
        assert "loss_ratio" in result.columns

    def test_groups_and_sorts(self, sample_df):
        result = aggregate_monthly(sample_df)
        assert result["month"].tolist() == ["2023-01", "2023-02"]
        jan = result[result["month"] == "2023-01"].iloc[0]
        assert jan["total_premium"] == 300.0
        assert jan["total_payout"] == 50.0
        assert jan["contract_count"] == 2
        # 50 / 300 * 100
        assert jan["loss_ratio"] == pytest.approx(50 / 300 * 100)


class TestAggregateByRegion:
    def test_values_and_sort(self, sample_df):
        result = aggregate_by_region(sample_df)
        # СПб: premium 700 > Москва 300 → идёт первым (сортировка по премии)
        assert result.iloc[0]["region"] == "СПб"
        spb = result[result["region"] == "СПб"].iloc[0]
        assert spb["total_premium"] == 700.0
        assert spb["claims_count"] == 1
        assert spb["loss_ratio"] == pytest.approx(600 / 700 * 100)


class TestAggregateByProduct:
    def test_claims_count(self, sample_df):
        result = aggregate_by_product(sample_df)
        osago = result[result["product"] == "ОСАГО"].iloc[0]
        assert osago["contract_count"] == 3
        assert osago["claims_count"] == 2
