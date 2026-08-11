import pandas as pd
import plotly.express as px
import streamlit as st

from pi4_imoveis_sp.ml.inference import load_model_metadata
from pi4_imoveis_sp.presentation import format_currency
from pi4_imoveis_sp.visualization import (
    PLOTLY_CHART_CONFIG,
    lock_chart_interactions,
)


@st.cache_data(show_spinner=False)
def load_metadata() -> dict:
    return load_model_metadata()


def main() -> None:
    st.title("Modelo de Machine Learning")

    st.write(
        "Desempenho, comparação e interpretação do modelo desenvolvido "
        "para estimar o valor de apartamentos residenciais em São Paulo."
    )

    st.caption(
        "O desempenho final foi medido em um período posterior ao utilizado "
        "para o treinamento, preservando a ordem temporal das transações."
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
            help=(
                "Erro Absoluto Médio. Representa, em média, "
                "a diferença absoluta entre o valor real "
                "e o valor estimado pelo modelo."
            ),
        )

    with metric_2:
        st.metric(
            "RMSE",
            format_currency(metrics["rmse"]),
            help=(
                "Raiz do Erro Quadrático Médio. Penaliza mais "
                "fortemente previsões com erros muito elevados."
            ),
        )

    with metric_3:
        st.metric(
            "R²",
            f"{metrics['r2']:.4f}",
            help=(
                "Coeficiente de determinação. Indica quanto da "
                "variação dos valores observados é explicada "
                "pelas previsões do modelo."
            ),
        )

    st.caption(
        "Avaliação temporal independente realizada em dezembro de 2025. "
        "O modelo foi treinado com os registros de janeiro a novembro."
    )

    st.info(
        "**Como interpretar:** valores menores de MAE e RMSE indicam "
        "menores erros de previsão. Para o R², valores mais próximos "
        "de 1 indicam maior capacidade de explicar a variação observada "
        "nos dados."
    )

    st.divider()

    st.subheader("Comparação dos modelos")

    st.write(
        "Diferentes algoritmos foram comparados antes da escolha "
        "da configuração utilizada pelo modelo."
    )

    model_results = pd.DataFrame(
        {
            "Modelo": [
                "Dummy",
                "Regressão Linear",
                "Random Forest",
                "XGBoost inicial (com mês)",
                "XGBoost selecionado (sem mês)",
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

        mae_chart = lock_chart_interactions(mae_chart)

        st.plotly_chart(
            mae_chart,
            width="stretch",
            config=PLOTLY_CHART_CONFIG,
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

        r2_chart = lock_chart_interactions(r2_chart)

        st.plotly_chart(
            r2_chart,
            width="stretch",
            config=PLOTLY_CHART_CONFIG,
        )

    st.caption(
        "As comparações acima utilizam novembro como conjunto "
        "de validação. O resultado final em dezembro foi mantido "
        "separado durante a seleção do modelo."
    )

    st.divider()

    st.subheader("Importância das variáveis")

    st.write(
        "A análise abaixo mostra quanto o desempenho do modelo piora "
        "quando a informação de cada variável é embaralhada."
    )

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
            "Aumento do MAE": ("Aumento do MAE após permutação (R$)"),
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

    importance_chart = lock_chart_interactions(importance_chart)

    st.plotly_chart(
        importance_chart,
        width="stretch",
        config=PLOTLY_CHART_CONFIG,
    )

    st.caption(
        "A importância foi calculada por Permutation Importance. "
        "Valores maiores indicam maior perda de desempenho quando "
        "a informação da variável é embaralhada."
    )

    st.info(
        "A importância indica contribuição para a capacidade preditiva "
        "do modelo. Ela não demonstra que uma variável causa diretamente "
        "o aumento ou a redução do valor de um imóvel."
    )

    st.divider()

    st.subheader("Configuração do modelo")

    config_1, config_2 = st.columns(2)

    with config_1:
        st.markdown(
            """
            **Algoritmo final:** XGBoost

            **Variáveis utilizadas:**
            - Área construída
            - CEP4
            - Padrão IPTU
            - Idade do imóvel
            - Fração ideal
            """
        )

        st.caption(
            "CEP4 corresponde aos quatro primeiros dígitos do CEP "
            "e é utilizado pelo modelo como informação aproximada "
            "de localização."
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
        "O desempenho do modelo foi inferior para imóveis de valores "
        "muito elevados e para alguns padrões menos frequentes. "
        "Esses segmentos devem ser interpretados com maior cautela."
    )

    st.write(
        "No conjunto final de dezembro, metade das previsões apresentou "
        "erro absoluto inferior a aproximadamente R$ 83 mil. Entretanto, "
        "um pequeno grupo de imóveis de alto valor apresentou erros muito "
        "elevados, aumentando principalmente o RMSE."
    )

    st.caption(
        "As métricas apresentadas nesta página correspondem à avaliação "
        "do modelo e não representam garantia de precisão para uma "
        "estimativa individual."
    )


main()
