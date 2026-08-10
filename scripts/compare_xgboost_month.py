from pi4_imoveis_sp.ml.xgboost_model import (
    XGBoostMetrics,
    run_xgboost,
)


def print_metrics(
    title: str,
    metrics: XGBoostMetrics,
) -> None:
    print(f"\n{title}")
    print("-" * 80)

    print(f"MAE:  R$ {metrics.mae:,.2f}")
    print(f"RMSE: R$ {metrics.rmse:,.2f}")
    print(f"R²:   {metrics.r2:.4f}")


def main() -> None:
    print("=" * 80)
    print("COMPARAÇÃO XGBOOST — COM MÊS VS. SEM MÊS")
    print("=" * 80)

    print("\nTreino: janeiro a outubro.")
    print("Validação: novembro.")
    print("Dezembro permanece reservado para teste final.")

    print("\nTreinando modelo COM mês...")
    with_month = run_xgboost(
        include_month=True,
    )

    print("Treinando modelo SEM mês...")
    without_month = run_xgboost(
        include_month=False,
    )

    print_metrics(
        "XGBOOST — COM MÊS",
        with_month,
    )

    print_metrics(
        "XGBOOST — SEM MÊS",
        without_month,
    )

    print("\nDIFERENÇA — SEM MÊS MENOS COM MÊS")
    print("-" * 80)

    print(f"MAE:  R$ {without_month.mae - with_month.mae:,.2f}")

    print(f"RMSE: R$ {without_month.rmse - with_month.rmse:,.2f}")

    print(f"R²:   {without_month.r2 - with_month.r2:+.4f}")

    print("\n" + "=" * 80)
    print("COMPARAÇÃO CONCLUÍDA")
    print("=" * 80)


if __name__ == "__main__":
    main()
