import polars as pl
import streamlit as st
from sklearn.pipeline import Pipeline

from pi4_imoveis_sp.data.cleaning import PROCESSED_FILE
from pi4_imoveis_sp.ml.inference import (
    load_model_metadata,
    load_production_model,
    predict_apartment_price,
)

REFERENCE_YEAR = 2025


@st.cache_resource(show_spinner=False)
def load_model() -> Pipeline:
    return load_production_model()


@st.cache_data(show_spinner=False)
def load_metadata() -> dict:
    return load_model_metadata()


@st.cache_data(show_spinner=False)
def load_reference_data() -> pl.DataFrame:
    dataframe = pl.read_parquet(PROCESSED_FILE)

    return dataframe.filter(
        ~pl.col("flag_valor_m2_muito_baixo")
        & ~pl.col("flag_transacao_muito_abaixo_vvr")
    )


def format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"

    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    return f"R$ {formatted}"


def normalize_cep(cep: str) -> str:
    return "".join(character for character in cep if character.isdigit())


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

        if description:
            options[code] = f"{code} — {description}"
        else:
            options[code] = str(code)

    return options


def main() -> None:
    st.title("Estimador de Valor")

    st.write(
        "Informe as características do apartamento para obter "
        "uma estimativa de valor com o modelo XGBoost."
    )

    model = load_model()
    metadata = load_metadata()
    reference_data = load_reference_data()

    pattern_options = get_pattern_options(reference_data)

    known_cep4 = set(reference_data.get_column("cep4").unique().to_list())

    with st.form("estimator_form"):
        st.subheader("Características do imóvel")

        column_1, column_2 = st.columns(2)

        with column_1:
            area = st.number_input(
                "Área construída (m²)",
                min_value=1.0,
                max_value=3_000.0,
                value=80.0,
                step=1.0,
            )

            cep = st.text_input(
                "CEP",
                placeholder="Ex.: 04303-000",
                help=(
                    "O modelo utiliza os quatro primeiros "
                    "dígitos do CEP como informação de localização."
                ),
            )

            construction_year = st.number_input(
                "Ano de construção / ACC",
                min_value=1919,
                max_value=2025,
                value=2010,
                step=1,
                help=(
                    "Use preferencialmente o ano de conclusão "
                    "da construção registrado no IPTU."
                ),
            )

        with column_2:
            iptu_pattern = st.selectbox(
                "Padrão IPTU",
                options=list(pattern_options),
                format_func=lambda code: pattern_options[code],
                help=("Código de padrão construtivo utilizado no cadastro do IPTU."),
            )

            ideal_fraction = st.number_input(
                "Fração ideal",
                min_value=0.0001,
                max_value=1.0,
                value=0.0100,
                step=0.0001,
                format="%.4f",
                help=(
                    "Fração ideal do terreno associada à unidade, "
                    "conforme cadastro do imóvel."
                ),
            )

        submitted = st.form_submit_button(
            "Estimar valor",
            type="primary",
            width="stretch",
        )

    if not submitted:
        st.caption(
            "A estimativa é baseada exclusivamente nas características "
            "informadas e nos dados do ITBI de 2025."
        )
        return

    normalized_cep = normalize_cep(cep)

    if len(normalized_cep) != 8:
        st.error("Informe um CEP válido com 8 dígitos.")
        return

    cep4 = normalized_cep[:4]

    if cep4 not in known_cep4:
        st.warning(
            "O prefixo deste CEP não apareceu nos dados utilizados "
            "para treinamento. A estimativa pode apresentar menor "
            "confiabilidade para essa localização."
        )

    property_age = REFERENCE_YEAR - construction_year

    prediction = predict_apartment_price(
        area=area,
        cep4=cep4,
        iptu_pattern=iptu_pattern,
        property_age=property_age,
        ideal_fraction=ideal_fraction,
        model=model,
    )

    estimated_value_m2 = prediction / area

    st.divider()

    st.subheader("Resultado da estimativa")

    result_1, result_2 = st.columns(2)

    with result_1:
        st.metric(
            "Valor estimado",
            format_currency(prediction),
        )

    with result_2:
        st.metric(
            "Valor estimado por m²",
            format_currency(estimated_value_m2),
        )

    st.markdown(
        f"""
        **Dados utilizados na previsão**

        - Área construída: **{area:,.0f} m²**
        - CEP informado: **{cep}**
        - Região utilizada pelo modelo (CEP4): **{cep4}**
        - Padrão IPTU: **{iptu_pattern}**
        - Ano de construção / ACC: **{construction_year}**
        - Idade utilizada pelo modelo: **{property_age} anos**
        - Fração ideal: **{ideal_fraction:.4f}**
        """
    )

    official_metrics = metadata["official_evaluation"]["metrics"]

    st.info(
        "Esta é uma estimativa estatística, não uma avaliação "
        "imobiliária oficial. No teste temporal independente, "
        f"o modelo apresentou MAE de "
        f"{format_currency(official_metrics['mae'])}."
    )

    if prediction >= 5_000_000:
        st.warning(
            "Imóveis de alto valor apresentaram maior erro durante "
            "a avaliação do modelo. Interprete esta estimativa com "
            "cautela."
        )


main()
