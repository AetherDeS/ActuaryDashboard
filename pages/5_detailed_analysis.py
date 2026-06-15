"""Страница: Детальный анализ."""

import plotly.express as px
import streamlit as st

from config import COLORS
from utils.formatters import format_currency
from utils.loader import load_filtered_data, render_sidebar, validate_filters
from utils.ui import page_heading, setup_page

setup_page("Детальный анализ", "search")
render_sidebar()
page_heading("search", "Детальный анализ")

if not validate_filters():
    st.stop()

with st.spinner("Загрузка данных..."):
    df = load_filtered_data()

if df.empty:
    st.warning("Нет данных за выбранный период.")
    st.stop()

with st.expander("Фильтрация таблицы"):
    search_id = st.text_input("Поиск по ID договора", "")
    search_region = st.text_input("Поиск по региону", "")
    search_product = st.text_input("Поиск по продукту", "")

filtered = df.copy()
if search_id:
    filtered = filtered[filtered["contract_id"].str.contains(search_id, case=False, na=False)]
if search_region:
    filtered = filtered[filtered["region"].str.contains(search_region, case=False, na=False)]
if search_product:
    filtered = filtered[filtered["product"].str.contains(search_product, case=False, na=False)]

st.caption(f"Найдено договоров: {len(filtered)}")

PAGE_SIZE = 50
total_pages = max(1, (len(filtered) - 1) // PAGE_SIZE + 1)
page = st.number_input("Страница", min_value=1, max_value=total_pages, value=1, step=1)
start_idx = (page - 1) * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE

display_cols = [
    "contract_id", "region", "product", "premium", "payout",
    "start_date", "end_date", "client_age", "client_gender",
]
page_df = filtered[display_cols].iloc[start_idx:end_idx].copy()
page_df["premium"] = page_df["premium"].apply(format_currency)
page_df["payout"] = page_df["payout"].apply(format_currency)
page_df.columns = [
    "ID договора", "Регион", "Продукт", "Премия", "Выплата",
    "Начало", "Окончание", "Возраст", "Пол",
]

st.dataframe(page_df, use_container_width=True, hide_index=True)

with st.sidebar:
    st.divider()
    st.subheader("Карточка договора")
    contract_ids = filtered["contract_id"].tolist()
    if contract_ids:
        selected_id = st.selectbox("Выберите договор", contract_ids, key="detail_contract")
        contract = filtered[filtered["contract_id"] == selected_id].iloc[0]

        st.markdown(f"**ID:** {contract['contract_id']}")
        st.markdown(f"**Регион:** {contract['region']}")
        st.markdown(f"**Продукт:** {contract['product']}")
        st.markdown(f"**Премия:** {format_currency(contract['premium'])}")
        st.markdown(f"**Выплата:** {format_currency(contract['payout'])}")
        st.markdown(
            f"**Период:** {contract['start_date'].date()} — {contract['end_date'].date()}"
        )
        st.markdown(f"**Клиент:** {contract['client_age']} лет, {contract['client_gender']}")
    else:
        st.info("Нет договоров для отображения.")

st.subheader("Статистика клиентов")
col1, col2 = st.columns(2)

with col1:
    fig_age = px.histogram(
        df,
        x="client_age",
        nbins=20,
        title="Распределение по возрасту клиентов",
        labels={"client_age": "Возраст"},
        color_discrete_sequence=[COLORS["blue"]],
    )
    st.plotly_chart(fig_age, use_container_width=True)

with col2:
    gender_stats = df.groupby("client_gender").size().reset_index(name="count")
    fig_gender = px.pie(
        gender_stats,
        values="count",
        names="client_gender",
        title="Распределение по полу",
        labels={"client_gender": "Пол", "count": "Количество"},
        color_discrete_sequence=[COLORS["blue"], COLORS["orange"]],
    )
    st.plotly_chart(fig_gender, use_container_width=True)
