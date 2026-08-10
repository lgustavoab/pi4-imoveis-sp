from pi4_imoveis_sp.ml.baseline import run_baselines


def print_metrics(
    model_name: str,
    mae: float,
    rmse: float,
    r2: float,
) -> None:
    print(f"\n{model_name}")
    print("-" * 80)

    print(f"MAE:  R$ {mae:,.2f}")
    print(f"RMSE: R$ {rmse:,.2f}")
    print(f"R²:   {r2:.4f}")


def main() -> None:
    print("=" * 80)
    print("BASELINES DE REGRESSÃO — ITBI 2025")
    print("=" * 80)

    print("\nTreinando com janeiro a outubro.")
    print("Avaliando exclusivamente em novembro.")
    print("Dezembro permanece reservado para teste final.")

    results = run_baselines()

    print_metrics(
        "BASELINE 0 — DUMMY REGRESSOR (MEDIANA)",
        results.dummy.mae,
        results.dummy.rmse,
        results.dummy.r2,
    )

    print_metrics(
        "BASELINE 1 — REGRESSÃO LINEAR",
        results.linear.mae,
        results.linear.rmse,
        results.linear.r2,
    )

    print("\n" + "=" * 80)
    print("AVALIAÇÃO DE BASELINE CONCLUÍDA")
    print("=" * 80)


if __name__ == "__main__":
    main()
