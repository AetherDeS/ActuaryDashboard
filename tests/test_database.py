"""Тесты слоя данных SQLite (data/database.py)."""

import pandas as pd
from sqlalchemy import text

from data.database import Database
from data.generator import DataGenerator


def _make_db(tmp_path, n=200):
    db = Database(str(tmp_path / "test.db"))
    db.init_database()
    db.insert_data(DataGenerator(n).generate())
    return db


def test_normalized_tables_created(tmp_path):
    db = _make_db(tmp_path, 200)
    try:
        with db._get_engine().connect() as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
            }
        assert {"regions", "products", "clients", "contracts", "payouts"} <= tables
    finally:
        db.close()


def test_payouts_match_claims(tmp_path):
    db = _make_db(tmp_path, 500)
    try:
        flat = db.get_contracts()
        claims = int((flat["payout"] > 0).sum())
        with db._get_engine().connect() as conn:
            payout_rows = conn.execute(text("SELECT COUNT(*) FROM payouts")).scalar()
            contract_rows = conn.execute(text("SELECT COUNT(*) FROM contracts")).scalar()
        assert payout_rows == claims
        assert contract_rows == 500
    finally:
        db.close()


def test_roundtrip_returns_all_rows(tmp_path):
    db = _make_db(tmp_path, 200)
    try:
        out = db.get_contracts()
        assert len(out) == 200
        assert pd.api.types.is_datetime64_any_dtype(out["start_date"])
    finally:
        db.close()


def test_region_filter(tmp_path):
    db = _make_db(tmp_path, 300)
    try:
        all_df = db.get_contracts()
        region = all_df["region"].iloc[0]
        filtered = db.get_contracts({"regions": [region]})
        assert not filtered.empty
        assert (filtered["region"] == region).all()
    finally:
        db.close()


def test_product_filter(tmp_path):
    db = _make_db(tmp_path, 300)
    try:
        all_df = db.get_contracts()
        product = all_df["product"].iloc[0]
        filtered = db.get_contracts({"products": [product]})
        assert not filtered.empty
        assert (filtered["product"] == product).all()
    finally:
        db.close()


def test_region_stats_loss_ratio_finite(tmp_path):
    db = _make_db(tmp_path, 500)
    try:
        stats = db.get_region_stats()
        assert not stats.empty
        assert not stats["loss_ratio"].isin([float("inf"), float("-inf")]).any()
        assert not stats["loss_ratio"].isna().any()
    finally:
        db.close()


def test_monthly_stats_columns(tmp_path):
    db = _make_db(tmp_path, 300)
    try:
        stats = db.get_monthly_stats()
        assert {"month", "total_premium", "total_payout", "contract_count"} <= set(stats.columns)
    finally:
        db.close()
