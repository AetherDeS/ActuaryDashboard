"""Тесты генератора тестовых данных (data/generator.py)."""

from data.generator import DataGenerator

EXPECTED_COLUMNS = {
    "contract_id", "region", "product", "premium", "payout",
    "start_date", "end_date", "client_age", "client_gender",
}


def test_row_count_and_columns():
    df = DataGenerator(500).generate()
    assert len(df) == 500
    assert set(df.columns) == EXPECTED_COLUMNS


def test_deterministic_across_calls():
    df1 = DataGenerator(300).generate()
    df2 = DataGenerator(300).generate()
    assert df1.equals(df2)


def test_premium_floor():
    df = DataGenerator(1000).generate()
    assert df["premium"].min() >= 5000


def test_claim_share_near_thirty_percent():
    df = DataGenerator(5000).generate()
    share = (df["payout"] > 0).mean()
    assert 0.27 <= share <= 0.33


def test_age_within_range():
    df = DataGenerator(1000).generate()
    assert df["client_age"].min() >= 18
    assert df["client_age"].max() <= 70


def test_end_date_after_start_date():
    df = DataGenerator(500).generate()
    assert (df["end_date"] > df["start_date"]).all()


def test_no_payout_without_claim():
    df = DataGenerator(1000).generate()
    assert (df["payout"] >= 0).all()
