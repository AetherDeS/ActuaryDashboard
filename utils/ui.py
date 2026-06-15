"""Общие UI-компоненты: иконки, стили, заголовки страниц."""

import streamlit as st

MATERIAL_SYMBOLS_URL = (
    "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
    ":opsz,wght,FILL,GRAD@24,300,0,0&display=swap"
)

NAV_ITEMS = [
    ("Главная", "", "home"),
    ("Обзор и KPI", "overview_kpi", "analytics"),
    ("Премии и выплаты", "premiums_payouts", "payments"),
    ("Регионы и продукты", "regions_products", "map"),
    ("Сезонность", "seasonality", "trending_up"),
    ("Детальный анализ", "detailed_analysis", "search"),
]

GLOBAL_STYLES = f"""
<style>
@import url('{MATERIAL_SYMBOLS_URL}');

.material-symbols-outlined {{
    font-family: 'Material Symbols Outlined';
    font-weight: normal;
    font-style: normal;
    font-size: 1.35rem;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
    color: var(--text-color);
    vertical-align: middle;
    opacity: 0.8;
}}

.page-heading {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin: 0 0 0.25rem 0;
}}

.page-heading h1 {{
    margin: 0;
    padding: 0;
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.2;
}}

.nav-link {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    margin: 0.15rem 0;
    border-radius: 0.5rem;
    text-decoration: none !important;
    color: var(--text-color) !important;
    font-size: 0.9rem;
    transition: background-color 0.2s ease;
}}

.nav-link:hover {{
    background-color: var(--secondary-background-color);
}}

.nav-link .material-symbols-outlined {{
    font-size: 1.1rem;
    text-decoration: none !important;
    color: var(--text-color) !important;
}}

/* Скрыть верхнее меню Streamlit, чтобы нельзя было поменять тему (и другие настройки) */
header[data-testid="stHeader"] {{
    display: none !important;
}}

/* Скрыть стандартную навигацию Streamlit (используем свою) */
[data-testid="stSidebarNav"] {{
    display: none !important;
}}

/* Убрать кнопку сворачивания — панель всегда открыта.
   Добавлены несколько вариантов селекторов для разных версий Streamlit. */
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarHeaderCollapsedControl"],
[data-testid="stExpandSidebarButton"],
[data-testid="collapsedControl"],
[data-testid="stBaseButton-headerNoPadding"],
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] button,
section[data-testid="stSidebar"] button[kind="header"],
section[data-testid="stSidebar"] button[kind="headerNoPadding"],
button[title="Collapse sidebar"],
button[title="Expand sidebar"],
button[aria-label="Collapse sidebar"],
button[aria-label="Expand sidebar"],
span[data-testid="stIconMaterialRounded"].keyboard_double_arrow_left,
span[data-testid="stIconMaterialRounded"].keyboard_double_arrow_right {{
    display: none !important;
}}

/* Жестко скрыть системный header сайдбара вместе с кнопкой */
section[data-testid="stSidebar"] div[data-testid="stSidebarHeader"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    min-height: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    overflow: hidden !important;
}}

section[data-testid="stSidebar"] div[data-testid="stSidebarHeader"] * {{
    display: none !important;
}}

/* Принудительно держать сайдбар раскрытым, даже если браузер запомнил
   свёрнутое состояние (иначе без кнопки разворота панель не открыть) */
section[data-testid="stSidebar"] {{
    display: block !important;
    visibility: visible !important;
    transform: none !important;
    margin-left: 0 !important;
    width: 244px !important;
    min-width: 244px !important;
}}

section[data-testid="stSidebar"][aria-expanded="false"] {{
    transform: none !important;
    margin-left: 0 !important;
    width: 244px !important;
    min-width: 244px !important;
}}

/* Скрыть верхний блок сайдбара (там была кнопка сворачивания),
   чтобы навигация по страницам шла первой */
[data-testid="stSidebarHeader"] {{
    display: none !important;
}}

section[data-testid="stSidebar"] > div {{
    padding-top: 0 !important;
}}

section[data-testid="stSidebar"] .block-container {{
    padding-top: 0 !important;
}}
</style>
"""


def inject_global_styles() -> None:
    """Подключить Material Symbols и глобальные стили."""
    st.markdown(GLOBAL_STYLES, unsafe_allow_html=True)


def setup_page(
    title: str,
    icon: str = "dashboard",
    *,
    layout: str = "wide",
    sidebar_state: str = "expanded",
) -> None:
    """Настройка страницы: конфиг и стили."""
    kwargs = {
        "page_title": title,
        "layout": layout,
        "initial_sidebar_state": sidebar_state,
    }
    try:
        st.set_page_config(page_icon=f":material/{icon}:", **kwargs)
    except Exception:
        st.set_page_config(**kwargs)
    inject_global_styles()


def render_navigation() -> None:
    """Кастомная навигация с русскими названиями и иконками."""
    links = []
    for label, slug, icon in NAV_ITEMS:
        href = "/" if not slug else f"/{slug}"
        links.append(
            f'<a class="nav-link" href="{href}" target="_self">'
            f'<span class="material-symbols-outlined">{icon}</span>{label}</a>'
        )
    st.sidebar.markdown(
        f'<div style="margin-bottom:0;">{"".join(links)}</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()


def page_heading(icon: str, title: str) -> None:
    """Заголовок страницы с иконкой из Material Symbols."""
    st.markdown(
        f"""
        <div class="page-heading">
            <span class="material-symbols-outlined">{icon}</span>
            <h1>{title}</h1>
        </div>
        """,
        unsafe_allow_html=True,
    )
