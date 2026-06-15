"""Страница: Сезонность."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import COLORS, MONTH_NAMES_RU
from utils.aggregations import aggregate_monthly
from utils.calculations import forecast_next_period
from utils.formatters import format_currency
from utils.loader import load_filtered_data, render_sidebar, validate_filters
from utils.ui import page_heading, setup_page

FORECAST_METHOD_LABELS = {
    "linear_regression": "линейная регрессия",
    "moving_average": "скользящее среднее",
}

setup_page("Сезонность", "trending_up")
render_sidebar()
page_heading("trending_up", "Сезонность")

if not validate_filters():
    st.stop()

with st.spinner("Загрузка данных..."):
    df = load_filtered_data()

if df.empty:
    st.warning("Нет данных за выбранный период.")
    st.stop()

df_s = df.copy()
df_s["year"] = df_s["start_date"].dt.year
df_s["month_num"] = df_s["start_date"].dt.month
df_s["month_name"] = df_s["month_num"].map(MONTH_NAMES_RU)

tab1, tab2, tab3 = st.tabs([
    "Тепловая карта премий",
    "Сезонность",
    "Страховые случаи",
])

with tab1:
    heat = df_s.groupby(["year", "month_num"]).agg(premium=("premium", "sum")).reset_index()
    heat["month_name"] = heat["month_num"].map(MONTH_NAMES_RU)
    pivot = heat.pivot(index="month_name", columns="year", values="premium").fillna(0)
    month_order = [MONTH_NAMES_RU[i] for i in range(1, 13)]
    pivot = pivot.reindex([m for m in month_order if m in pivot.index])

    fig_heat = px.imshow(
        pivot,
        title="Тепловая карта: сумма премий (месяцы × годы)",
        labels=dict(x="Год", y="Месяц", color="Премии, ₽"),
        color_continuous_scale="Blues",
        aspect="auto",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab2:
    seasonal = df_s.groupby("month_num").agg(
        avg_premium=("premium", "mean"),
        total_premium=("premium", "sum"),
        month_name=("month_name", "first"),
    ).reset_index().sort_values("month_num")

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=seasonal["month_name"],
        y=seasonal["total_premium"],
        mode="lines+markers",
        name="Сумма премий",
        line=dict(color=COLORS["blue"], width=2),
    ))
    fig_line.update_layout(
        title="Сезонность: сумма премий по месяцам (усреднение за все годы)",
        xaxis_title="Месяц",
        yaxis_title="Сумма премий, ₽",
    )
    st.plotly_chart(fig_line, use_container_width=True)

with tab3:
    claims = df_s[df_s["payout"] > 0].groupby("month_num").size().reset_index(name="claims")
    claims["month_name"] = claims["month_num"].map(MONTH_NAMES_RU)
    claims = claims.sort_values("month_num")

    fig_claims = px.bar(
        claims,
        x="month_name",
        y="claims",
        title="Распределение страховых случаев по месяцам",
        labels={"month_name": "Месяц", "claims": "Количество случаев"},
        color_discrete_sequence=[COLORS["orange"]],
    )
    st.plotly_chart(fig_claims, use_container_width=True)

payout_by_month = df_s.groupby("month_num").agg(total_payout=("payout", "sum")).reset_index()
payout_by_month["month_name"] = payout_by_month["month_num"].map(MONTH_NAMES_RU)
peak_months = payout_by_month.nlargest(3, "total_payout")

st.subheader("Анализ сезонности")
st.markdown(
    f"**Пик выплат** приходится на месяцы: "
    f"{', '.join(peak_months['month_name'].tolist())} "
    f"с суммарными выплатами "
    f"{', '.join(format_currency(v) for v in peak_months['total_payout'].tolist())}."
)

premium_by_month = df_s.groupby("month_num").agg(total_premium=("premium", "sum")).reset_index()
peak_premium = premium_by_month.nlargest(1, "total_premium").iloc[0]
st.markdown(
    f"**Пик премий** — {MONTH_NAMES_RU[int(peak_premium['month_num'])]} "
    f"({format_currency(peak_premium['total_premium'])})."
)

st.subheader("Прогноз на следующие 3 месяца")
monthly = aggregate_monthly(df)

history_points = len(monthly)
forecast = forecast_next_period(monthly.set_index("month"), "total_premium", periods=3)

if forecast.empty:
    st.info("Недостаточно данных для построения прогноза за выбранный период.")
else:
    method_key = forecast["type"].iloc[0]
    method_label = FORECAST_METHOD_LABELS.get(method_key, method_key)

    if method_key == "moving_average":
        st.warning(
            f"Мало данных для регрессии (всего {history_points} мес. истории) — "
            "прогноз построен по скользящему среднему и носит ориентировочный характер. "
            "Расширьте период в фильтрах для более надёжного прогноза."
        )

    fig_fc = go.Figure()
    fig_fc.add_trace(go.Bar(
        x=forecast["period"],
        y=forecast["forecast"],
        marker_color=COLORS["green"],
        name="Прогноз премий",
    ))
    fig_fc.update_layout(
        title="Прогноз премий на 3 месяца",
        yaxis_title="Прогноз, ₽",
        xaxis_title="Период",
    )
    st.plotly_chart(fig_fc, use_container_width=True)
    st.caption(f"Метод прогнозирования: {method_label} (история: {history_points} мес.)")
