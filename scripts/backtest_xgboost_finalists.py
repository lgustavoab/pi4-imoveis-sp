from datetime import date
from math import isclose
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
    "CANDIDATO A — DEPTH 8 / 800 ÁRVORES": {
        "max_depth": 8,
        "learning_rate": 0.05,
        "n_estimators": 800,
    },
    "CANDIDATO B — DEPTH 8 / 500 ÁRVORES": {
        "max_depth": 8,
        "learning_rate": 0.05,
        "n_estimators": 500,
    },
    "CANDIDATO C — DEPTH 6 / 800 ÁRVORES": {
        "max_depth": 6,
        "learning_rate": 0.05,
        "n_estimators": 800,
    },
}

EXPECTED_WINDOW_ROWS = {
    7: (30_718, 5_331),
    8: (36_049, 5_366),
    9: (41_415, 5_509),
    10: (46_924, 5_883),
    11: (52_807, 4_902),
}

MAE_TIE_ABSOLUTE_TOLERANCE = 0.01


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
        transaction_start=date(TRANSACTION_YEAR, 1, 1),
        transaction_end=date(TRANSACTION_YEAR, 12, 1),
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

            expected_train_rows, expected_validation_rows = EXPECTED_WINDOW_ROWS[
                validation_month
            ]

            if train.height != expected_train_rows:
                raise ValueError(
                    f"Treino inesperado para o mês {validation_month:02d}: "
                    f"{train.height:,}. Esperado: {expected_train_rows:,}."
                )

            if validation.height != expected_validation_rows:
                raise ValueError(
                    f"Validação inesperada para o mês {validation_month:02d}: "
                    f"{validation.height:,}. Esperado: {expected_validation_rows:,}."
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
                    "month": validation_month,
                    "train_rows": train.height,
                    "validation_rows": validation.height,
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

    monthly_wins = {name: 0 for name in CANDIDATES}

    for month_index, _ in enumerate(VALIDATION_MONTHS):
        minimum_monthly_mae = min(
            candidate_results[month_index]["mae"]
            for candidate_results in results.values()
        )

        for candidate_name, candidate_results in results.items():
            if isclose(
                candidate_results[month_index]["mae"],
                minimum_monthly_mae,
                rel_tol=0.0,
                abs_tol=MAE_TIE_ABSOLUTE_TOLERANCE,
            ):
                monthly_wins[candidate_name] += 1

    summary: dict[str, dict[str, float | int]] = {}

    for candidate_name, candidate_results in results.items():
        maes = [result["mae"] for result in candidate_results]

        rmses = [result["rmse"] for result in candidate_results]

        r2_scores = [result["r2"] for result in candidate_results]

        mean_mae = mean(maes)
        mean_rmse = mean(rmses)
        mean_r2 = mean(r2_scores)
        mae_std = pstdev(maes)

        summary[candidate_name] = {
            "mean_mae": mean_mae,
            "mae_std": mae_std,
            "minimum_mae": min(maes),
            "maximum_mae": max(maes),
            "mean_rmse": mean_rmse,
            "mean_r2": mean_r2,
            "monthly_wins": monthly_wins[candidate_name],
        }

        print(f"\n{candidate_name}")
        print("-" * 80)

        print(f"MAE médio:       R$ {mean_mae:,.2f}")
        print(f"Desvio MAE:      R$ {mae_std:,.2f}")
        print(f"Menor MAE:       R$ {min(maes):,.2f}")
        print(f"Maior MAE:       R$ {max(maes):,.2f}")
        print(f"RMSE médio:      R$ {mean_rmse:,.2f}")
        print(f"R² médio:        {mean_r2:.4f}")
        print(f"Vitórias mensais: {monthly_wins[candidate_name]}")

    ranking = sorted(
        summary,
        key=lambda candidate_name: summary[candidate_name]["mean_mae"],
    )

    winner = ranking[0]
    runner_up = ranking[1]

    if isclose(
        summary[winner]["mean_mae"],
        summary[runner_up]["mean_mae"],
        rel_tol=0.0,
        abs_tol=MAE_TIE_ABSOLUTE_TOLERANCE,
    ):
        print("\n" + "=" * 80)
        print("EMPATE EFETIVO NO MAE MÉDIO")
        print("=" * 80)
        print(winner)
        print(runner_up)
        print("Nenhum modelo foi selecionado automaticamente.")
        return

    print("\n" + "=" * 80)
    print("VENCEDOR — MENOR MAE MÉDIO")
    print("=" * 80)

    print(winner)
    print(f"MAE médio: R$ {summary[winner]['mean_mae']:,.2f}")


if __name__ == "__main__":
    main()
