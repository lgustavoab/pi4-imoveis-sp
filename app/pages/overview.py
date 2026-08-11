import plotly.express as px
import polars as pl
import streamlit as st

from pi4_imoveis_sp.analysis.overview import (
    PRICE_RANGES,
    add_price_ranges,
    apply_filters,
    build_analysis_dataset,
)
from pi4_imoveis_sp.data.cleaning import (
    AREA_COLUMN,
    PROCESSED_FILE,
    VALUE_COLUMN,
)
from pi4_imoveis_sp.presentation import (
    build_pattern_label,
    format_currency,
    format_integer,
)
from pi4_imoveis_sp.visualization import (
    PLOTLY_CHART_CONFIG,
    lock_chart_interactions,
)

MONTH_NAMES = {
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

PRICE_ORDER = [
    "Até R$ 300 mil",
    "R$ 300–500 mil",
    "R$ 500 mil–1 mi",
    "R$ 1–2 mi",
    "R$ 2–5 mi",
    "Acima de R$ 5 mi",
]


@st.cache_data(show_spinner=False)
def load_data() -> pl.DataFrame:
    return pl.read_parquet(PROCESSED_FILE)


def get_pattern_options(
    dataframe: pl.DataFrame,
) -> dict[int, str]:
    patterns = (
        dataframe.select(
            [
                "Padrão (IPTU)",
                "Descrição do padrão (IPTU)",
            ]
        )
        .unique()
        .sort("Padrão (IPTU)")
    )

    options: dict[int, str] = {}

    for row in patterns.iter_rows(named=True):
        code = row["Padrão (IPTU)"]
        description = row["Descrição do padrão (IPTU)"]

        if code is None:
            continue

        options[code] = build_pattern_label(
            code=code,
            description=description,
        )

    return options


def reset_filters(
    minimum_area: int,
    maximum_area: int,
) -> None:
    st.session_state["overview_price_range"] = "Todas as faixas"
    st.session_state["overview_months"] = []
    st.session_state["overview_patterns"] = []
    st.session_state["overview_min_area"] = minimum_area
    st.session_state["overview_max_area"] = maximum_area
    st.session_state["overview_cep4"] = []


def main() -> None:
    st.title("Visão Geral")

    st.write(
        "Explore as transações de apartamentos residenciais "
        "registradas no ITBI da cidade de São Paulo em 2025."
    )

    st.caption(
        "Os valores apresentados correspondem ao valor de transação "
        "declarado pelo contribuinte e aos registros considerados "
        "economicamente válidos após o tratamento dos dados."
    )

    dataframe = load_data()

    analysis_data = build_analysis_dataset(dataframe)

    pattern_options = get_pattern_options(analysis_data)

    month_options = sorted(analysis_data.get_column("mes_transacao").unique().to_list())

    cep4_options = sorted(analysis_data.get_column("cep4").unique().to_list())

    minimum_available_area = int(analysis_data.get_column(AREA_COLUMN).min())

    maximum_available_area = int(analysis_data.get_column(AREA_COLUMN).max())

    with st.expander(
        "Filtros da análise",
        expanded=True,
    ):
        filter_1, filter_2, filter_3 = st.columns(3)

        with filter_1:
            selected_price_range = st.selectbox(
                "Faixa de preço",
                options=list(PRICE_RANGES),
                index=0,
                key="overview_price_range",
            )

        with filter_2:
            selected_months = st.multiselect(
                "Mês da transação",
                options=month_options,
                format_func=lambda month: MONTH_NAMES[month],
                placeholder="Todos os meses",
                key="overview_months",
            )

        with filter_3:
            selected_patterns = st.multiselect(
                "Padrão IPTU",
                options=list(pattern_options),
                format_func=lambda code: pattern_options[code],
                placeholder="Todos os padrões",
                key="overview_patterns",
            )

        filter_4, filter_5, filter_6 = st.columns(3)

        with filter_4:
            minimum_area = st.number_input(
                "Área mínima (m²)",
                min_value=minimum_available_area,
                max_value=maximum_available_area,
                value=minimum_available_area,
                step=1,
                key="overview_min_area",
            )

        with filter_5:
            maximum_area = st.number_input(
                "Área máxima (m²)",
                min_value=minimum_available_area,
                max_value=maximum_available_area,
                value=maximum_available_area,
                step=1,
                key="overview_max_area",
            )

        with filter_6:
            selected_cep4 = st.multiselect(
                "Prefixo do CEP (CEP4)",
                options=cep4_options,
                placeholder="Todos os prefixos",
                help=(
                    "CEP4 corresponde aos quatro primeiros "
                    "dígitos do CEP. Ele é utilizado como uma "
                    "aproximação da localização do imóvel."
                ),
                key="overview_cep4",
            )

        caption_column, button_column = st.columns([5, 1])

        with caption_column:
            st.caption(
                "Campos de seleção vazios representam todos os valores disponíveis."
            )

        with button_column:
            st.button(
                "Limpar filtros",
                on_click=reset_filters,
                args=(
                    minimum_available_area,
                    maximum_available_area,
                ),
                width="stretch",
            )

    if minimum_area > maximum_area:
        st.error("A área mínima não pode ser maior que a área máxima.")
        return

    filtered_data = apply_filters(
        dataframe=analysis_data,
        selected_months=selected_months,
        selected_patterns=selected_patterns,
        selected_cep4=selected_cep4,
        selected_price_range=selected_price_range,
        minimum_area=minimum_area,
        maximum_area=maximum_area,
    )

    if filtered_data.height == 0:
        st.warning("Nenhum apartamento corresponde aos filtros selecionados.")
        return

    median_value = filtered_data.select(pl.col(VALUE_COLUMN).median()).item()

    median_area = filtered_data.select(pl.col(AREA_COLUMN).median()).item()

    median_value_m2 = filtered_data.select(pl.col("valor_m2").median()).item()

    percentage = filtered_data.height / analysis_data.height * 100

    st.subheader("Resumo do recorte")

    metric_1, metric_2, metric_3, metric_4 = st.columns(4)

    with metric_1:
        st.metric(
            "Apartamentos no recorte",
            format_integer(filtered_data.height),
        )

    with metric_2:
        st.metric(
            "Valor mediano",
            format_currency(median_value),
        )

    with metric_3:
        st.metric(
            "Área mediana",
            f"{format_integer(round(median_area))} m²",
        )

    with metric_4:
        st.metric(
            "Valor mediano por m²",
            format_currency(median_value_m2),
        )

    st.caption(
        f"O recorte atual representa "
        f"{percentage:.2f}% dos "
        f"{format_integer(analysis_data.height)} "
        "registros economicamente válidos. "
        f"A base processada completa contém "
        f"{format_integer(dataframe.height)} "
        "apartamentos."
    )

    st.divider()

    monthly_data = (
        filtered_data.group_by("mes_transacao")
        .agg(
            pl.len().alias("transacoes"),
            pl.col(VALUE_COLUMN).median().alias("valor_mediano"),
        )
        .sort("mes_transacao")
        .with_columns(
            pl.col("mes_transacao")
            .replace_strict(
                MONTH_NAMES,
                return_dtype=pl.String,
            )
            .alias("mês")
        )
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

        transactions_chart = lock_chart_interactions(transactions_chart)

        st.plotly_chart(
            transactions_chart,
            width="stretch",
            config=PLOTLY_CHART_CONFIG,
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
            rangemode="tozero",
        )

        median_chart = lock_chart_interactions(median_chart)

        st.plotly_chart(
            median_chart,
            width="stretch",
            config=PLOTLY_CHART_CONFIG,
        )

    st.divider()

    st.subheader("Distribuição por faixa de preço")

    price_ranges = add_price_ranges(filtered_data).group_by("faixa_preco").len()

    price_chart = px.bar(
        price_ranges.to_pandas(),
        x="faixa_preco",
        y="len",
        category_orders={
            "faixa_preco": PRICE_ORDER,
        },
        labels={
            "faixa_preco": "Faixa de preço",
            "len": "Apartamentos",
        },
    )

    price_chart.update_layout(
        showlegend=False,
    )

    price_chart = lock_chart_interactions(price_chart)

    st.plotly_chart(
        price_chart,
        width="stretch",
        config=PLOTLY_CHART_CONFIG,
    )

    st.divider()

    st.caption(
        "Fonte dos dados: Prefeitura de São Paulo — Guias de ITBI pagas em 2025."
    )


main()
