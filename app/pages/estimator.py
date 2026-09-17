import polars as pl
import streamlit as st
from sklearn.pipeline import Pipeline

from pi4_imoveis_sp.analysis.estimator import (
    format_cep,
    get_pattern_options,
    normalize_cep,
)
from pi4_imoveis_sp.data.cleaning import PROCESSED_FILE
from pi4_imoveis_sp.ml.inference import (
    load_model_metadata,
    load_production_model,
    predict_apartment_price,
)
from pi4_imoveis_sp.presentation import (
    format_currency,
    format_integer,
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


def main() -> None:
    st.title("Estimador de Valor")

    st.write(
        "Informe as características do imóvel para obter "
        "uma estimativa do valor de transação utilizando "
        "o modelo XGBoost."
    )

    st.caption(
        "A previsão representa uma estimativa estatística do valor "
        "de transação declarado. Ela não corresponde ao valor venal, "
        "ao preço de anúncio e não substitui uma avaliação imobiliária."
    )

    model = load_model()
    metadata = load_metadata()
    reference_data = load_reference_data()
    production_training_rows = metadata["production_training_rows"]

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
                help=(
                    "Informe preferencialmente a área "
                    "construída registrada no cadastro "
                    "do IPTU."
                ),
            )

            cep = st.text_input(
                "CEP",
                placeholder="Ex.: 04303-000",
                help=(
                    "O CEP completo é utilizado para obter o CEP4, "
                    "formado pelos quatro primeiros dígitos. "
                    "O modelo utiliza o CEP4 como informação "
                    "aproximada de localização."
                ),
            )

            construction_year = st.number_input(
                "Ano de conclusão da construção (ACC)",
                min_value=1919,
                max_value=REFERENCE_YEAR,
                value=2010,
                step=1,
                help=(
                    "ACC corresponde ao Ano de Conclusão "
                    "da Construção registrado no cadastro "
                    "do IPTU. Utilize esse valor quando "
                    "estiver disponível."
                ),
            )

        with column_2:
            iptu_pattern = st.selectbox(
                "Padrão construtivo do IPTU",
                options=list(pattern_options),
                index=None,
                placeholder=("Selecione o padrão do imóvel"),
                format_func=lambda code: pattern_options[code],
                help=(
                    "Os códigos representam padrões construtivos "
                    "diferentes. Mesmo quando dois códigos possuem "
                    "a mesma descrição geral, eles podem representar "
                    "padrões distintos. Utilize preferencialmente "
                    "o código presente no cadastro do imóvel."
                ),
            )

            ideal_fraction = st.number_input(
                "Fração ideal",
                min_value=0.0001,
                max_value=1.0,
                value=0.0100,
                step=0.0001,
                format="%.4f",
                help=(
                    "Representa a fração do terreno associada "
                    "à unidade no cadastro do imóvel. "
                    "Informe o valor em formato decimal. "
                    "Por exemplo, 0.0100 corresponde a 1%."
                ),
            )

        st.caption(
            "Para obter uma estimativa mais coerente com os dados "
            "utilizados no treinamento, informe as características "
            "conforme constam no cadastro do imóvel sempre que possível."
        )

        submitted = st.form_submit_button(
            "Estimar valor",
            type="primary",
            width="stretch",
        )

    if not submitted:
        st.caption(
            f"O modelo de produção foi treinado nos "
            f"{format_integer(production_training_rows)} registros "
            "economicamente válidos com Data de Transação em 2025."
        )
        return

    if iptu_pattern is None:
        st.error("Selecione o padrão construtivo do IPTU.")
        return

    normalized_cep = normalize_cep(cep)

    if len(normalized_cep) != 8:
        st.error("Informe um CEP válido com 8 dígitos.")
        return

    formatted_cep = format_cep(normalized_cep)

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

    selected_pattern_label = pattern_options[iptu_pattern]

    formatted_area = format_integer(round(area))

    ideal_fraction_percentage = ideal_fraction * 100

    st.divider()

    st.subheader("Resultado da estimativa")

    result_1, result_2 = st.columns(2)

    with result_1:
        st.metric(
            "Valor de transação estimado",
            format_currency(prediction),
        )

    with result_2:
        st.metric(
            "Valor estimado por m²",
            format_currency(estimated_value_m2),
        )

    st.caption(
        "O valor por m² acima é calculado a partir da estimativa "
        "gerada pelo modelo e da área construída informada."
    )

    st.markdown(
        f"""
        **Dados utilizados na previsão**

        - Área construída: **{formatted_area} m²**
        - CEP informado: **{formatted_cep}**
        - Região utilizada pelo modelo (CEP4): **{cep4}**
        - Padrão IPTU: **{selected_pattern_label}**
        - Ano de conclusão da construção (ACC): **{construction_year}**
        - Idade utilizada pelo modelo: **{property_age} anos**
        - Fração ideal: **{ideal_fraction:.4f} ({ideal_fraction_percentage:.2f}%)**
        """
    )

    official_metrics = metadata["official_evaluation"]["metrics"]

    st.info(
        "Esta é uma estimativa estatística e não uma avaliação "
        "imobiliária oficial. No teste temporal independente "
        "realizado em dezembro de 2025, o modelo apresentou MAE de "
        f"{format_currency(official_metrics['mae'])}. "
        "Esse valor representa o erro absoluto médio do conjunto "
        "avaliado e não uma margem de erro fixa para cada previsão."
    )

    if prediction >= 5_000_000:
        st.warning(
            "No teste final, a faixa de imóveis com valor declarado a partir "
            "de R$ 5 milhões apresentou erros substancialmente maiores. "
            "Esta observação descreve o grupo avaliado e não constitui uma "
            "margem de erro individual; interprete a estimativa com cautela."
        )

    st.divider()

    st.caption(
        "Fonte dos dados: Prefeitura de São Paulo — Guias de ITBI pagas em 2025."
    )


main()
