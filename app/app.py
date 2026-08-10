from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent
PAGES_DIR = APP_DIR / "pages"


st.set_page_config(
    page_title="Imóveis SP",
    page_icon="🏙️",
    layout="wide",
)


overview_page = st.Page(
    PAGES_DIR / "overview.py",
    title="Visão Geral",
    icon="📊",
    default=True,
)

model_page = st.Page(
    PAGES_DIR / "model.py",
    title="Modelo",
    icon="🤖",
)

estimator_page = st.Page(
    PAGES_DIR / "estimator.py",
    title="Estimador",
    icon="🏠",
)

navigation = st.navigation(
    [
        overview_page,
        model_page,
        estimator_page,
    ]
)

navigation.run()
