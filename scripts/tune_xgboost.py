from itertools import product

from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from xgboost import XGBRegressor

from pi4_imoveis_sp.ml.split import build_temporal_split
from pi4_imoveis_sp.ml.xgboost_model import build_preprocessor


def main() -> None:
    print("=" * 80)
    print("TUNING XGBOOST — ITBI 2025")
    print("=" * 80)

    print("\nTreino: janeiro a outubro.")
    print("Validação: novembro.")
    print("Dezembro permanece reservado para teste final.")
    print("Feature mes_transacao: removida.")

    split = build_temporal_split(
        include_month=False,
    )

    x_train = split.x_train.to_pandas()
    y_train = split.y_train.to_numpy()

    x_validation = split.x_validation.to_pandas()
    y_validation = split.y_validation.to_numpy()

    preprocessor = build_preprocessor(
        include_month=False,
    )

    x_train_processed = preprocessor.fit_transform(
        x_train,
    )

    x_validation_processed = preprocessor.transform(
        x_validation,
    )

    parameter_grid = {
        "max_depth": (4, 6, 8),
        "learning_rate": (0.03, 0.05),
        "n_estimators": (500, 800),
    }

    combinations = list(
        product(
            parameter_grid["max_depth"],
            parameter_grid["learning_rate"],
            parameter_grid["n_estimators"],
        )
    )

    print(f"\nCombinações que serão testadas: {len(combinations)}")

    best_result = None

    for index, (
        max_depth,
        learning_rate,
        n_estimators,
    ) in enumerate(
        combinations,
        start=1,
    ):
        print(
            f"\n[{index}/{len(combinations)}] "
            f"depth={max_depth}, "
            f"lr={learning_rate}, "
            f"estimators={n_estimators}"
        )

        model = XGBRegressor(
            objective="reg:squarederror",
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            min_child_weight=1,
            subsample=0.8,
            colsample_bytree=0.8,
            reg_lambda=1.0,
            tree_method="hist",
            random_state=42,
            n_jobs=-1,
        )

        model.fit(
            x_train_processed,
            y_train,
        )

        predictions = model.predict(
            x_validation_processed,
        )

        mae = float(
            mean_absolute_error(
                y_validation,
                predictions,
            )
        )

        rmse = float(
            root_mean_squared_error(
                y_validation,
                predictions,
            )
        )

        r2 = float(
            r2_score(
                y_validation,
                predictions,
            )
        )

        print(f"MAE:  R$ {mae:,.2f}")
        print(f"RMSE: R$ {rmse:,.2f}")
        print(f"R²:   {r2:.4f}")

        result = {
            "max_depth": max_depth,
            "learning_rate": learning_rate,
            "n_estimators": n_estimators,
            "mae": mae,
            "rmse": rmse,
            "r2": r2,
        }

        if best_result is None or mae < best_result["mae"]:
            best_result = result

    if best_result is None:
        raise RuntimeError("Nenhum resultado foi produzido pelo tuning.")

    print("\n" + "=" * 80)
    print("MELHOR CONFIGURAÇÃO — CRITÉRIO: MAE")
    print("=" * 80)

    print(f"max_depth:    {best_result['max_depth']}")

    print(f"learning_rate: {best_result['learning_rate']}")

    print(f"n_estimators: {best_result['n_estimators']}")

    print(f"\nMAE:  R$ {best_result['mae']:,.2f}")

    print(f"RMSE: R$ {best_result['rmse']:,.2f}")

    print(f"R²:   {best_result['r2']:.4f}")

    print("\n" + "=" * 80)
    print("TUNING CONCLUÍDO")
    print("=" * 80)


if __name__ == "__main__":
    main()
