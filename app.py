"""
Актуарный дашборд — главная страница.

Запуск:
    pip install -r requirements.txt
    streamlit run app.py
"""

import plotly.graph_objects as go
import streamlit as st

from config import COLORS
from utils.aggregations import aggregate_monthly
from utils.calculations import calculate_loss_ratio
from utils.formatters import format_currency, format_integer, format_percent
from utils.loader import load_filtered_data, render_sidebar, validate_filters
from utils.ui import page_heading, setup_page

setup_page("Главная", "home")
render_sidebar()

page_heading("home", "Актуарный дашборд")
st.markdown("Система анализа страховых данных для актуариев")

if not validate_filters():
    st.stop()

with st.spinner("Загрузка данных..."):
    df = load_filtered_data()

if df.empty:
    st.warning("Нет данных за выбранный период. Измените фильтры.")
    st.stop()

total_premium = df["premium"].sum()
total_payout = df["payout"].sum()
loss_ratio = calculate_loss_ratio(total_premium, total_payout)
contract_count = len(df)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Собрано премий", format_currency(total_premium))
with col2:
    st.metric("Выплачено", format_currency(total_payout))
with col3:
    st.metric("Коэффициент убыточности", format_percent(loss_ratio))
with col4:
    st.metric("Количество договоров", format_integer(contract_count))

st.subheader("Премии и выплаты по месяцам")

monthly = aggregate_monthly(df)

fig = go.Figure()
fig.add_trace(go.Bar(
    x=monthly["month"],
    y=monthly["total_premium"],
    name="Премии",
    marker_color=COLORS["blue"],
))
fig.add_trace(go.Bar(
    x=monthly["month"],
    y=monthly["total_payout"],
    name="Выплаты",
    marker_color=COLORS["orange"],
))
fig.update_layout(
    barmode="group",
    title="Премии и выплаты по месяцам",
    xaxis_title="Месяц",
    yaxis_title="Сумма, ₽",
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig, use_container_width=True)

st.info(
    "Используйте боковую панель для фильтрации данных. "
    "Перейдите на страницы в меню слева для детального анализа."
)
