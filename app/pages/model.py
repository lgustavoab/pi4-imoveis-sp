import pandas as pd
import plotly.express as px
import streamlit as st

from pi4_imoveis_sp.ml.inference import load_model_metadata
from pi4_imoveis_sp.presentation import format_currency, format_integer
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
    production_training_rows = metadata["production_training_rows"]

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
        "Avaliação temporal independente realizada em 5.431 registros de "
        "dezembro de 2025. O modelo de avaliação foi treinado em 57.709 "
        "registros de janeiro a novembro."
    )

    st.info(
        "O modelo foi congelado antes da abertura do teste de dezembro, que "
        "não participou da seleção nem do ajuste. As métricas pertencem ao "
        "modelo de avaliação temporal; não são uma avaliação do artefato de "
        f"produção posteriormente treinado nos "
        f"{format_integer(production_training_rows)} "
        "registros válidos de 2025."
    )

    st.subheader("Leitura dos erros no teste final")

    error_1, error_2, error_3, error_4 = st.columns(4)

    with error_1:
        st.metric("Mediana do erro absoluto", "R$ 84.607,78")

    with error_2:
        st.metric("Previsões acima do real", "53,31%")

    with error_3:
        st.metric("Previsões abaixo do real", "46,69%")

    with error_4:
        st.metric("Erro assinado médio", "-R$ 30.398,29")

    st.caption(
        "Esses valores descrevem o conjunto de dezembro. O MAE é uma média "
        "do conjunto e não uma margem fixa para cada apartamento."
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
                "XGBoost inicial (sem mês)",
                "XGBoost ajustado",
            ],
            "MAE": [
                445_690.03,
                312_417.38,
                185_435.77,
                184_440.95,
                181_962.60,
                170_133.00,
            ],
            "RMSE": [
                1_359_439.91,
                859_369.42,
                658_238.14,
                481_673.15,
                463_993.37,
                462_107.92,
            ],
            "R²": [
                -0.0464,
                0.5818,
                0.7547,
                0.8686,
                0.8781,
                0.8791,
            ],
        }
    )

    displayed_model_results = model_results.copy()
    displayed_model_results["MAE"] = displayed_model_results["MAE"].map(format_currency)
    displayed_model_results["RMSE"] = displayed_model_results["RMSE"].map(
        format_currency
    )
    displayed_model_results["R²"] = displayed_model_results["R²"].map(
        lambda value: f"{value:.4f}"
    )

    st.dataframe(
        displayed_model_results,
        hide_index=True,
        width="stretch",
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
        "A tabela e os gráficos desta seção utilizam exclusivamente a "
        "validação de novembro de 2025. O teste final de dezembro foi "
        "mantido separado durante toda a seleção do modelo."
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
                460_785.14,
                124_343.02,
                82_576.24,
                23_649.95,
                15_721.82,
            ],
            "Desvio": [
                6_331.58,
                3_620.19,
                5_289.14,
                1_499.60,
                2_524.52,
            ],
        }
    )

    displayed_importance = feature_importance.copy()
    displayed_importance["Aumento do MAE"] = displayed_importance["Aumento do MAE"].map(
        format_currency
    )
    displayed_importance["Desvio"] = displayed_importance["Desvio"].map(format_currency)

    st.dataframe(
        displayed_importance,
        hide_index=True,
        width="stretch",
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
        "Importância preditiva não representa causalidade. O resultado é "
        "específico deste modelo e do teste de dezembro; não representa "
        "valorização causada por uma variável."
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
            - `objective = reg:squarederror`
            - `max_depth = 8`
            - `learning_rate = 0.05`
            - `n_estimators = 800`
            - `min_child_weight = 1`
            - `subsample = 0.8`
            - `colsample_bytree = 0.8`
            - `reg_lambda = 1.0`
            - `tree_method = hist`
            - `random_state = 42`
            - `n_jobs = -1`
            """
        )

    st.divider()

    st.subheader("Limitações observadas")

    st.warning(
        "No teste, os 76 imóveis com valor declarado a partir de R$ 5 "
        "milhões (1,40% dos casos) apresentaram MAE de R$ 3.585.343,55, "
        "mediana do erro absoluto de R$ 1.656.100,00 e RMSE de "
        "R$ 7.957.496,16. Estimativas nessa faixa exigem cautela adicional."
    )

    st.write(
        "O alvo é o valor de transação declarado pelo contribuinte: não é "
        "preço de anúncio, valor venal ou avaliação profissional. O modelo "
        "não dispõe de características como estado de conservação, vagas, "
        "andar, vista e atributos internos. Os dados estão restritos às "
        "transações de 2025, e as diferenças de erro entre grupos não "
        "demonstram causalidade."
    )

    st.caption(
        "As métricas apresentadas nesta página correspondem à avaliação "
        "do modelo e não representam garantia de precisão para uma "
        "estimativa individual."
    )


main()
