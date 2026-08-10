import pandas as pd
import plotly.express as px
import streamlit as st

from pi4_imoveis_sp.ml.inference import load_model_metadata


@st.cache_data(show_spinner=False)
def load_metadata() -> dict:
    return load_model_metadata()


def format_currency(value: float) -> str:
    formatted = f"{value:,.2f}"

    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")

    return f"R$ {formatted}"


def main() -> None:
    st.title("Modelo de Machine Learning")

    st.write(
        "Desempenho e interpretação do modelo desenvolvido para "
        "estimar o valor de apartamentos residenciais em São Paulo."
    )

    metadata = load_metadata()

    official_evaluation = metadata["official_evaluation"]
    metrics = official_evaluation["metrics"]

    st.subheader("Avaliação final")

    metric_1, metric_2, metric_3 = st.columns(3)

    with metric_1:
        st.metric(
            "MAE",
            format_currency(metrics["mae"]),
        )

    with metric_2:
        st.metric(
            "RMSE",
            format_currency(metrics["rmse"]),
        )

    with metric_3:
        st.metric(
            "R²",
            f"{metrics['r2']:.4f}",
        )

    st.caption(
        "Avaliação temporal independente realizada em dezembro de 2025. "
        "O modelo foi treinado com os registros de janeiro a novembro."
    )

    st.divider()

    st.subheader("Comparação dos modelos")

    model_results = pd.DataFrame(
        {
            "Modelo": [
                "Dummy",
                "Regressão Linear",
                "Random Forest",
                "XGBoost inicial",
                "XGBoost selecionado",
            ],
            "MAE": [
                445_167.17,
                312_022.97,
                185_138.04,
                189_014.61,
                171_495.65,
            ],
            "R²": [
                -0.0463,
                0.5815,
                0.7597,
                0.8555,
                0.8707,
            ],
        }
    )

    chart_1, chart_2 = st.columns(2)

    with chart_1:
        st.markdown("#### Erro absoluto médio na validação")

        mae_chart = px.bar(
            model_results,
            x="Modelo",
            y="MAE",
            text_auto=".3s",
            labels={
                "MAE": "MAE (R$)",
            },
        )

        mae_chart.update_layout(
            showlegend=False,
        )

        mae_chart.update_yaxes(
            tickprefix="R$ ",
        )

        st.plotly_chart(
            mae_chart,
            width="stretch",
        )

    with chart_2:
        st.markdown("#### Coeficiente de determinação")

        r2_chart = px.bar(
            model_results,
            x="Modelo",
            y="R²",
            text_auto=".3f",
        )

        r2_chart.update_layout(
            showlegend=False,
        )

        st.plotly_chart(
            r2_chart,
            width="stretch",
        )

    st.caption(
        "As comparações acima utilizam novembro como conjunto "
        "de validação. O resultado final em dezembro foi mantido "
        "separado durante a seleção do modelo."
    )

    st.divider()

    st.subheader("Importância das variáveis")

    feature_importance = pd.DataFrame(
        {
            "Variável": [
                "Área construída",
                "CEP4",
                "Idade do imóvel",
                "Padrão IPTU",
                "Fração ideal",
            ],
            "Aumento do MAE": [
                461_077.29,
                122_226.73,
                76_834.99,
                22_185.82,
                13_649.87,
            ],
        }
    )

    feature_importance = feature_importance.sort_values(
        "Aumento do MAE",
        ascending=True,
    )

    importance_chart = px.bar(
        feature_importance,
        x="Aumento do MAE",
        y="Variável",
        orientation="h",
        text="Aumento do MAE",
        labels={
            "Aumento do MAE": "Aumento do MAE após permutação (R$)",
            "Variável": "",
        },
    )

    importance_chart.update_traces(
        texttemplate="R$ %{x:,.0f}",
        textposition="outside",
    )

    importance_chart.update_layout(
        showlegend=False,
        height=420,
        xaxis_range=[
            0,
            feature_importance["Aumento do MAE"].max() * 1.15,
        ],
    )

    importance_chart.update_xaxes(
        tickprefix="R$ ",
        rangemode="tozero",
    )

    st.plotly_chart(
        importance_chart,
        width="stretch",
    )

    st.caption(
        "A importância foi calculada por Permutation Importance. "
        "Valores maiores indicam maior perda de desempenho quando "
        "a informação da variável é embaralhada."
    )

    st.divider()

    st.subheader("Configuração do modelo")

    config_1, config_2 = st.columns(2)

    with config_1:
        st.markdown(
            """
            **Algoritmo final:** XGBoost

            **Features utilizadas:**
            - Área construída
            - CEP4
            - Padrão IPTU
            - Idade do imóvel
            - Fração ideal
            """
        )

    with config_2:
        st.markdown(
            """
            **Hiperparâmetros principais:**
            - `max_depth = 8`
            - `learning_rate = 0.05`
            - `n_estimators = 800`
            - `subsample = 0.8`
            - `colsample_bytree = 0.8`
            """
        )

    st.divider()

    st.subheader("Limitações observadas")

    st.warning(
        "O desempenho do modelo diminui para imóveis de valores "
        "muito elevados e padrões superiores, principalmente devido "
        "à menor quantidade de exemplos e à maior heterogeneidade "
        "desse segmento."
    )

    st.write(
        "No conjunto final de dezembro, metade das previsões apresentou "
        "erro absoluto inferior a aproximadamente R$ 83 mil. Entretanto, "
        "um pequeno grupo de imóveis de alto valor apresentou erros muito "
        "elevados, aumentando principalmente o RMSE."
    )

    st.info(
        "As importâncias apresentadas representam contribuição preditiva "
        "para o modelo e não devem ser interpretadas como relações causais."
    )


main()
