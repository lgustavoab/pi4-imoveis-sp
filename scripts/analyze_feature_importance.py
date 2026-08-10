from sklearn.inspection import permutation_importance

from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS_WITHOUT_MONTH,
)
from pi4_imoveis_sp.ml.final_model import (
    run_final_evaluation,
)


def main() -> None:
    print("=" * 80)
    print("IMPORTÂNCIA DAS FEATURES — XGBOOST")
    print("=" * 80)

    print("\nTreino do modelo: janeiro a novembro.")
    print("Análise de importância: dezembro.")
    print("Métrica utilizada: MAE.")

    evaluation = run_final_evaluation()

    x_test = evaluation.test_data.select(FEATURE_COLUMNS_WITHOUT_MONTH).to_pandas()

    print("\nCalculando permutation importance...")

    result = permutation_importance(
        evaluation.pipeline,
        x_test,
        evaluation.y_test,
        scoring="neg_mean_absolute_error",
        n_repeats=10,
        random_state=42,
        n_jobs=-1,
    )

    feature_results = []

    for feature, importance, deviation in zip(
        FEATURE_COLUMNS_WITHOUT_MONTH,
        result.importances_mean,
        result.importances_std,
        strict=True,
    ):
        feature_results.append(
            (
                feature,
                float(importance),
                float(deviation),
            )
        )

    feature_results.sort(
        key=lambda item: item[1],
        reverse=True,
    )

    print("\nIMPORTÂNCIA POR FEATURE")
    print("-" * 80)

    for position, (
        feature,
        importance,
        deviation,
    ) in enumerate(
        feature_results,
        start=1,
    ):
        print(f"{position}. {feature}")

        print(f"   Aumento médio do MAE: R$ {importance:,.2f}")

        print(f"   Desvio: R$ {deviation:,.2f}")

    print("\n" + "=" * 80)
    print("ANÁLISE DE IMPORTÂNCIA CONCLUÍDA")
    print("=" * 80)


if __name__ == "__main__":
    main()
