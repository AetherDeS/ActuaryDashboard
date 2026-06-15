"""Страница: Премии и выплаты."""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from config import COLORS
from utils.aggregations import aggregate_monthly
from utils.calculations import calculate_frequency
from utils.formatters import format_currency, format_percent
from utils.loader import load_filtered_data, render_sidebar, validate_filters
from utils.ui import page_heading, setup_page

setup_page("Премии и выплаты", "payments")
render_sidebar()
page_heading("payments", "Премии и выплаты")

if not validate_filters():
    st.stop()

with st.spinner("Загрузка данных..."):
    df = load_filtered_data()

if df.empty:
    st.warning("Нет данных за выбранный период.")
    st.stop()

monthly = aggregate_monthly(df)

tab1, tab2 = st.tabs(["Помесячная динамика", "Кумулятивные суммы"])

with tab1:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(
            x=monthly["month"], y=monthly["total_premium"],
            name="Премии", marker_color=COLORS["blue"],
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Bar(
            x=monthly["month"], y=monthly["total_payout"],
            name="Выплаты", marker_color=COLORS["orange"],
        ),
        secondary_y=True,
    )
    fig.update_layout(
        title="Премии и выплаты по месяцам (две оси)",
        barmode="stack",
        hovermode="x unified",
    )
    fig.update_yaxes(title_text="Премии, ₽", secondary_y=False)
    fig.update_yaxes(title_text="Выплаты, ₽", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    monthly["cum_premium"] = monthly["total_premium"].cumsum()
    monthly["cum_payout"] = monthly["total_payout"].cumsum()

    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["cum_premium"],
        fill="tozeroy", name="Кумулятивные премии",
        line=dict(color=COLORS["blue"]),
    ))
    fig_area.add_trace(go.Scatter(
        x=monthly["month"], y=monthly["cum_payout"],
        fill="tozeroy", name="Кумулятивные выплаты",
        line=dict(color=COLORS["orange"]),
    ))
    fig_area.update_layout(
        title="Кумулятивные премии и выплаты",
        xaxis_title="Месяц",
        yaxis_title="Сумма, ₽",
    )
    st.plotly_chart(fig_area, use_container_width=True)

claims_count = (df["payout"] > 0).sum()
avg_premium = df["premium"].mean()
avg_payout = df.loc[df["payout"] > 0, "payout"].mean() if claims_count > 0 else 0
frequency = calculate_frequency(len(df), claims_count)

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Средняя премия на договор", format_currency(avg_premium))
with m2:
    st.metric("Средняя выплата", format_currency(avg_payout))
with m3:
    st.metric("Частота страховых случаев", format_percent(frequency))

col1, col2 = st.columns(2)

with col1:
    fig_scatter = px.scatter(
        df,
        x="premium",
        y="payout",
        color="product",
        title="Премия и выплата по договорам",
        labels={"premium": "Премия, ₽", "payout": "Выплата, ₽", "product": "Продукт"},
        color_discrete_sequence=[
            COLORS["blue"], COLORS["orange"], COLORS["green"],
            COLORS["red"], "#9467bd", "#8c564b",
        ],
        opacity=0.6,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    fig_hist = px.histogram(
        df,
        x="premium",
        nbins=40,
        title="Распределение премий",
        labels={"premium": "Премия, ₽"},
        color_discrete_sequence=[COLORS["blue"]],
    )
    st.plotly_chart(fig_hist, use_container_width=True)
