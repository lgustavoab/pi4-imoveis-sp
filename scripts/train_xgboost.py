from pi4_imoveis_sp.ml.xgboost_model import run_xgboost


def main() -> None:
    print("=" * 80)
    print("XGBOOST — ITBI 2025")
    print("=" * 80)

    print("\nTreino: janeiro a outubro.")
    print("Validação: novembro.")
    print("Dezembro permanece reservado para teste final.")

    metrics = run_xgboost()

    print("\nXGBOOST")
    print("-" * 80)

    print(f"MAE:  R$ {metrics.mae:,.2f}")
    print(f"RMSE: R$ {metrics.rmse:,.2f}")
    print(f"R²:   {metrics.r2:.4f}")

    print("\n" + "=" * 80)
    print("TREINAMENTO CONCLUÍDO")
    print("=" * 80)


if __name__ == "__main__":
    main()
