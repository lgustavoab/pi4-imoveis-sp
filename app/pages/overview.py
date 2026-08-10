import plotly.express as px
import polars as pl
import streamlit as st

from pi4_imoveis_sp.data.cleaning import (
    PROCESSED_FILE,
    VALUE_COLUMN,
)

AREA_COLUMN = "Área Construída (m2)"


@st.cache_data(show_spinner=False)
def load_data() -> pl.DataFrame:
    return pl.read_parquet(PROCESSED_FILE)


def format_integer(value: int) -> str:
    return f"{value:,}".replace(",", ".")


def format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"

    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    return f"R$ {formatted}"


def build_analysis_dataset(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    return dataframe.filter(
        ~pl.col("flag_valor_m2_muito_baixo")
        & ~pl.col("flag_transacao_muito_abaixo_vvr")
    ).with_columns(pl.col("Data de Transação").dt.month().alias("mes_transacao"))


def main() -> None:
    st.title("Visão Geral")

    st.write(
        "Panorama das transações de apartamentos residenciais "
        "na cidade de São Paulo registradas no ITBI de 2025."
    )

    dataframe = load_data()

    analysis_data = build_analysis_dataset(dataframe)

    median_value = analysis_data.select(pl.col(VALUE_COLUMN).median()).item()

    median_area = analysis_data.select(pl.col(AREA_COLUMN).median()).item()

    column_1, column_2, column_3, column_4 = st.columns(4)

    with column_1:
        st.metric(
            "Apartamentos analisados",
            format_integer(dataframe.height),
        )

    with column_2:
        st.metric(
            "Registros utilizados no modelo",
            format_integer(analysis_data.height),
        )

    with column_3:
        st.metric(
            "Valor mediano",
            format_currency(median_value),
        )

    with column_4:
        st.metric(
            "Área mediana",
            f"{median_area:,.0f} m²",
        )

    st.caption(
        "Os indicadores econômicos desconsideram registros "
        "classificados como anomalias econômicas severas."
    )

    st.divider()

    monthly_data = (
        analysis_data.group_by("mes_transacao")
        .agg(
            pl.len().alias("transacoes"),
            pl.col(VALUE_COLUMN).median().alias("valor_mediano"),
        )
        .sort("mes_transacao")
    )

    month_names = {
        1: "Jan",
        2: "Fev",
        3: "Mar",
        4: "Abr",
        5: "Mai",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Set",
        10: "Out",
        11: "Nov",
        12: "Dez",
    }

    monthly_data = monthly_data.with_columns(
        pl.col("mes_transacao")
        .replace_strict(
            month_names,
            return_dtype=pl.String,
        )
        .alias("mês")
    )

    chart_column_1, chart_column_2 = st.columns(2)

    with chart_column_1:
        st.subheader("Transações por mês")

        transactions_chart = px.bar(
            monthly_data.to_pandas(),
            x="mês",
            y="transacoes",
            labels={
                "mês": "Mês",
                "transacoes": "Transações",
            },
        )

        transactions_chart.update_layout(
            showlegend=False,
        )

        st.plotly_chart(
            transactions_chart,
            width="stretch",
        )

    with chart_column_2:
        st.subheader("Valor mediano por mês")

        median_chart = px.line(
            monthly_data.to_pandas(),
            x="mês",
            y="valor_mediano",
            markers=True,
            labels={
                "mês": "Mês",
                "valor_mediano": "Valor mediano",
            },
        )

        median_chart.update_layout(
            showlegend=False,
        )

        median_chart.update_yaxes(
            tickprefix="R$ ",
        )

        st.plotly_chart(
            median_chart,
            width="stretch",
        )

    st.divider()

    st.subheader("Distribuição por faixa de preço")

    price_ranges = (
        analysis_data.with_columns(
            pl.when(pl.col(VALUE_COLUMN) < 300_000)
            .then(pl.lit("Até R$ 300 mil"))
            .when(pl.col(VALUE_COLUMN) < 500_000)
            .then(pl.lit("R$ 300–500 mil"))
            .when(pl.col(VALUE_COLUMN) < 1_000_000)
            .then(pl.lit("R$ 500 mil–1 mi"))
            .when(pl.col(VALUE_COLUMN) < 2_000_000)
            .then(pl.lit("R$ 1–2 mi"))
            .when(pl.col(VALUE_COLUMN) < 5_000_000)
            .then(pl.lit("R$ 2–5 mi"))
            .otherwise(pl.lit("Acima de R$ 5 mi"))
            .alias("faixa_preco")
        )
        .group_by("faixa_preco")
        .len()
    )

    price_order = [
        "Até R$ 300 mil",
        "R$ 300–500 mil",
        "R$ 500 mil–1 mi",
        "R$ 1–2 mi",
        "R$ 2–5 mi",
        "Acima de R$ 5 mi",
    ]

    price_chart = px.bar(
        price_ranges.to_pandas(),
        x="faixa_preco",
        y="len",
        category_orders={
            "faixa_preco": price_order,
        },
        labels={
            "faixa_preco": "Faixa de preço",
            "len": "Apartamentos",
        },
    )

    price_chart.update_layout(
        showlegend=False,
    )

    st.plotly_chart(
        price_chart,
        width="stretch",
    )


main()
