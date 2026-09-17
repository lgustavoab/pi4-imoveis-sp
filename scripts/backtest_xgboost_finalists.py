from datetime import date
from statistics import mean, pstdev

import polars as pl
from sklearn.metrics import (
    mean_absolute_error,
    r2_score,
    root_mean_squared_error,
)
from xgboost import XGBRegressor

from pi4_imoveis_sp.data.cleaning import (
    TRANSACTION_DATE_COLUMN,
    TRANSACTION_YEAR,
)
from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS_WITHOUT_MONTH,
    TARGET_COLUMN,
    build_model_dataset,
)
from pi4_imoveis_sp.ml.xgboost_model import build_preprocessor

VALIDATION_MONTHS = (7, 8, 9, 10, 11)

CANDIDATES = {
    "CANDIDATO A — DEPTH 6": {
        "max_depth": 6,
        "learning_rate": 0.05,
        "n_estimators": 800,
    },
    "CANDIDATO B — DEPTH 8": {
        "max_depth": 8,
        "learning_rate": 0.05,
        "n_estimators": 800,
    },
}


def main() -> None:
    print("=" * 80)
    print("BACKTEST TEMPORAL — FINALISTAS XGBOOST")
    print("=" * 80)

    print("\nDezembro permanece reservado para o teste final.")
    print("Feature mes_transacao não é fornecida ao modelo.")
    print("Data de Transação restrita ao ano de 2025.")

    dataframe = build_model_dataset(
        exclude_severe_anomalies=True,
        include_month=False,
    )

    results: dict[str, list[dict[str, float]]] = {name: [] for name in CANDIDATES}

    for candidate_name, parameters in CANDIDATES.items():
        print("\n" + "=" * 80)
        print(candidate_name)
        print("=" * 80)

        for validation_month in VALIDATION_MONTHS:
            validation_start = date(
                TRANSACTION_YEAR,
                validation_month,
                1,
            )
            validation_end = date(
                TRANSACTION_YEAR,
                validation_month + 1,
                1,
            )

            train = dataframe.filter(
                (pl.col(TRANSACTION_DATE_COLUMN) >= date(TRANSACTION_YEAR, 1, 1))
                & (pl.col(TRANSACTION_DATE_COLUMN) < validation_start)
            )

            validation = dataframe.filter(
                (pl.col(TRANSACTION_DATE_COLUMN) >= validation_start)
                & (pl.col(TRANSACTION_DATE_COLUMN) < validation_end)
            )

            x_train = train.select(FEATURE_COLUMNS_WITHOUT_MONTH).to_pandas()

            y_train = train.get_column(TARGET_COLUMN).to_numpy()

            x_validation = validation.select(FEATURE_COLUMNS_WITHOUT_MONTH).to_pandas()

            y_validation = validation.get_column(TARGET_COLUMN).to_numpy()

            preprocessor = build_preprocessor(
                include_month=False,
            )

            x_train_processed = preprocessor.fit_transform(x_train)

            x_validation_processed = preprocessor.transform(x_validation)

            model = XGBRegressor(
                objective="reg:squarederror",
                max_depth=parameters["max_depth"],
                learning_rate=parameters["learning_rate"],
                n_estimators=parameters["n_estimators"],
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

            predictions = model.predict(x_validation_processed)

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

            results[candidate_name].append(
                {
                    "mae": mae,
                    "rmse": rmse,
                    "r2": r2,
                }
            )

            print(
                f"\nValidação mês {validation_month:02d} "
                f"| treino: {train.height:,} "
                f"| validação: {validation.height:,}"
            )

            print(f"MAE:  R$ {mae:,.2f}")
            print(f"RMSE: R$ {rmse:,.2f}")
            print(f"R²:   {r2:.4f}")

    print("\n" + "=" * 80)
    print("RESUMO DO BACKTEST")
    print("=" * 80)

    summary: dict[str, float] = {}

    for candidate_name, candidate_results in results.items():
        maes = [result["mae"] for result in candidate_results]

        rmses = [result["rmse"] for result in candidate_results]

        r2_scores = [result["r2"] for result in candidate_results]

        mean_mae = mean(maes)
        mean_rmse = mean(rmses)
        mean_r2 = mean(r2_scores)
        mae_std = pstdev(maes)

        summary[candidate_name] = mean_mae

        print(f"\n{candidate_name}")
        print("-" * 80)

        print(f"MAE médio:       R$ {mean_mae:,.2f}")
        print(f"Desvio MAE:      R$ {mae_std:,.2f}")
        print(f"RMSE médio:      R$ {mean_rmse:,.2f}")
        print(f"R² médio:        {mean_r2:.4f}")

    winner = min(
        summary,
        key=summary.get,
    )

    print("\n" + "=" * 80)
    print("VENCEDOR — MENOR MAE MÉDIO")
    print("=" * 80)

    print(winner)
    print(f"MAE médio: R$ {summary[winner]:,.2f}")


if __name__ == "__main__":
    main()
