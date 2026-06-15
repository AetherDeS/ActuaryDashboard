"""Генератор реалистичных тестовых данных для страховых договоров."""

from datetime import date

import numpy as np
import pandas as pd

from config import PRODUCTS, REGIONS

RANDOM_SEED = 42

# Горизонт дат начала договоров — последние 3 года
HISTORY_DAYS = 3 * 365


class DataGenerator:
    """Генерация тестовых данных по страховым договорам."""

    # Средние выплаты по продуктам (при наступлении страхового случая)
    PAYOUT_MEANS = {
        "ОСАГО": 80000,
        "КАСКО": 250000,
        "Страхование имущества": 150000,
        "Ипотека": 500000,
        "ДМС": 45000,
        "НС": 120000,
    }

    def __init__(self, n_contracts: int = 10000):
        self.n_contracts = n_contracts

    def generate(self) -> pd.DataFrame:
        """Сгенерировать DataFrame с договорами страхования (векторизованно)."""
        n = self.n_contracts
        rng = np.random.default_rng(RANDOM_SEED)

        products = rng.choice(PRODUCTS, size=n)
        regions = rng.choice(REGIONS, size=n)
        premiums = np.maximum(5000, rng.normal(50000, 15000, size=n))

        # Вероятность выплаты — 30%; сумма зависит от продукта
        has_claim = rng.random(n) < 0.30
        mean_payouts = np.array([self.PAYOUT_MEANS[p] for p in products])
        raw_payouts = np.maximum(0, rng.normal(mean_payouts, mean_payouts * 0.4))
        payouts = np.where(has_claim, raw_payouts, 0.0)

        today = pd.Timestamp(date.today())
        start_offsets = rng.integers(0, HISTORY_DAYS + 1, size=n)
        start_dates = today - pd.to_timedelta(start_offsets, unit="D")
        durations = rng.integers(180, 730, size=n)
        end_dates = start_dates + pd.to_timedelta(durations, unit="D")

        ages = rng.integers(18, 71, size=n)
        genders = rng.choice(["М", "Ж"], size=n)

        contract_ids = [f"CTR-{i:06d}" for i in range(1, n + 1)]

        return pd.DataFrame({
            "contract_id": contract_ids,
            "region": regions,
            "product": products,
            "premium": np.round(premiums, 2),
            "payout": np.round(payouts, 2),
            "start_date": start_dates,
            "end_date": end_dates,
            "client_age": ages,
            "client_gender": genders,
        })
