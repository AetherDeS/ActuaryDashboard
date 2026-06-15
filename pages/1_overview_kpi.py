"""Страница: Обзор и KPI."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import COLORS
from utils.aggregations import aggregate_by_product, aggregate_monthly
from utils.calculations import add_trend_line, calculate_loss_ratio, calculate_period_delta
from utils.formatters import format_currency, format_integer, format_percent, month_label
from utils.loader import get_previous_period_data, load_filtered_data, render_sidebar, validate_filters
from utils.ui import page_heading, setup_page

setup_page("Обзор и KPI", "analytics")
render_sidebar()
page_heading("analytics", "Обзор и KPI")

if not validate_filters():
    st.stop()

with st.spinner("Загрузка данных..."):
    df = load_filtered_data()
    df_prev = get_previous_period_data(df)

if df.empty:
    st.warning("Нет данных за выбранный период.")
    st.stop()

cur_premium = df["premium"].sum()
cur_payout = df["payout"].sum()
cur_loss = calculate_loss_ratio(cur_premium, cur_payout)
cur_count = len(df)

prev_premium = df_prev["premium"].sum() if not df_prev.empty else 0
prev_payout = df_prev["payout"].sum() if not df_prev.empty else 0
prev_loss = calculate_loss_ratio(prev_premium, prev_payout)
prev_count = len(df_prev) if not df_prev.empty else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(
        "Премии",
        format_currency(cur_premium),
        delta=f"{format_percent(calculate_period_delta(cur_premium, prev_premium), 2)}",
    )
with c2:
    st.metric(
        "Выплаты",
        format_currency(cur_payout),
        delta=f"{format_percent(calculate_period_delta(cur_payout, prev_payout), 2)}",
    )
with c3:
    st.metric(
        "Убыточность",
        format_percent(cur_loss),
        delta=f"{round(cur_loss - prev_loss, 2):.2f} п.п.",
        delta_color="inverse",
    )
with c4:
    st.metric(
        "Договоры",
        format_integer(cur_count),
        delta=f"{format_percent(calculate_period_delta(cur_count, prev_count), 2)}",
    )

tab1, tab2 = st.tabs(["Динамика убыточности", "Распределение продуктов"])

with tab1:
    monthly = aggregate_monthly(df)
    monthly["month_label"] = monthly["month"].apply(month_label)

    _, trend_y = add_trend_line(
        monthly["month_label"].tolist(),
        monthly["loss_ratio"].tolist(),
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly["month_label"],
        y=monthly["loss_ratio"],
        mode="lines+markers",
        name="Убыточность",
        line=dict(color=COLORS["blue"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=monthly["month_label"],
        y=trend_y,
        mode="lines",
        name="Тренд",
        line=dict(color=COLORS["red"], dash="dash"),
    ))
    fig.update_layout(
        title="Динамика коэффициента убыточности по месяцам",
        xaxis_title="Месяц",
        yaxis_title="Убыточность, %",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_a, col_b = st.columns(2)
    product_stats = aggregate_by_product(df)

    with col_a:
        fig_pie = px.pie(
            product_stats,
            values="total_premium",
            names="product",
            title="Доля премий по продуктам",
            color_discrete_sequence=[
                COLORS["blue"], COLORS["orange"], COLORS["green"],
                COLORS["red"], "#9467bd", "#8c564b",
            ],
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        fig_tree = px.treemap(
            product_stats,
            path=["product"],
            values="total_premium",
            title="Древовидная карта: объём премий по продуктам",
            color="total_premium",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_tree, use_container_width=True)

st.subheader("Топ-5 продуктов по объёму премий")
top5 = product_stats.head(5)[
    ["product", "total_premium", "total_payout", "contract_count", "loss_ratio"]
].copy()
top5["loss_ratio"] = top5["loss_ratio"].round(2)
top5 = top5.rename(columns={
    "product": "Продукт",
    "total_premium": "Премии",
    "total_payout": "Выплаты",
    "contract_count": "Договоры",
    "loss_ratio": "Убыточность, %",
})
st.dataframe(top5, use_container_width=True, hide_index=True)

csv_data = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    label="Экспорт данных в CSV",
    data=csv_data,
    file_name="contracts_export.csv",
    mime="text/csv",
)
