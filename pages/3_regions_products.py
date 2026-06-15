"""Страница: Регионы и продукты."""

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import COLORS
from utils.aggregations import aggregate_by_region, loss_ratio_series
from utils.formatters import format_currency, format_percent
from utils.loader import load_filtered_data, render_sidebar, validate_filters
from utils.ui import page_heading, setup_page

setup_page("Регионы и продукты", "map")
render_sidebar()
page_heading("map", "Регионы и продукты")

if not validate_filters():
    st.stop()

with st.spinner("Загрузка данных..."):
    df = load_filtered_data()

if df.empty:
    st.warning("Нет данных за выбранный период.")
    st.stop()

region_stats = aggregate_by_region(df)

tab1, tab2, tab3 = st.tabs([
    "Топ убыточных регионов",
    "Тепловая карта",
    "Пузырьковая диаграмма",
])

with tab1:
    top_loss = region_stats.sort_values("loss_ratio", ascending=True).head(10)
    fig_bar = go.Figure(go.Bar(
        x=top_loss["loss_ratio"],
        y=top_loss["region"],
        orientation="h",
        marker_color=[
            COLORS["red"] if lr > 100 else COLORS["blue"]
            for lr in top_loss["loss_ratio"]
        ],
        text=[format_percent(v, 2) for v in top_loss["loss_ratio"]],
        textposition="outside",
    ))
    fig_bar.update_layout(
        title="Топ-10 регионов по убыточности",
        xaxis_title="Убыточность, %",
        yaxis_title="Регион",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with tab2:
    heat_df = df.groupby(["region", "product"]).agg(
        premium=("premium", "sum"),
        payout=("payout", "sum"),
    ).reset_index()
    heat_df["loss_ratio"] = loss_ratio_series(heat_df["premium"], heat_df["payout"])
    pivot = heat_df.pivot(index="region", columns="product", values="loss_ratio").fillna(0)

    fig_heat = px.imshow(
        pivot,
        title="Тепловая карта: убыточность (регионы × продукты)",
        labels=dict(x="Продукт", y="Регион", color="Убыточность, %"),
        color_continuous_scale="RdYlGn_r",
        aspect="auto",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab3:
    fig_bubble = px.scatter(
        region_stats,
        x="total_premium",
        y="loss_ratio",
        size="contract_count",
        color="loss_ratio",
        hover_name="region",
        title="Регионы: размер — договоры, цвет — убыточность",
        labels={
            "total_premium": "Премии, ₽",
            "loss_ratio": "Убыточность, %",
            "contract_count": "Договоры",
        },
        color_continuous_scale="RdYlGn_r",
        size_max=60,
    )
    st.plotly_chart(fig_bubble, use_container_width=True)

st.subheader("Детализация по регионам")
display_df = region_stats[
    ["region", "total_premium", "total_payout", "contract_count", "loss_ratio"]
].copy()
display_df.columns = ["Регион", "Премии", "Выплаты", "Договоры", "Убыточность, %"]
display_df["Премии"] = display_df["Премии"].apply(format_currency)
display_df["Выплаты"] = display_df["Выплаты"].apply(format_currency)
display_df["Убыточность, %"] = display_df["Убыточность, %"].apply(
    lambda x: format_percent(x, 2)
)


def highlight_high_loss(row):
    val = float(row["Убыточность, %"].replace("%", "").replace(",", "."))
    if val > 100:
        return ["color: #d62728; font-weight: bold;"] * len(row)
    return [""] * len(row)


st.dataframe(
    display_df.style.apply(highlight_high_loss, axis=1),
    use_container_width=True,
    hide_index=True,
)

high_loss_regions = region_stats[region_stats["loss_ratio"] > 100]["region"].tolist()
if high_loss_regions:
    st.error(f"Регионы с убыточностью > 100%: {', '.join(high_loss_regions)}")
