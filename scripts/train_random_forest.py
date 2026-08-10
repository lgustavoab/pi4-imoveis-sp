from pi4_imoveis_sp.ml.random_forest import run_random_forest


def main() -> None:
    print("=" * 80)
    print("RANDOM FOREST — ITBI 2025")
    print("=" * 80)

    print("\nTreino: janeiro a outubro.")
    print("Validação: novembro.")
    print("Dezembro permanece reservado para teste final.")

    metrics = run_random_forest()

    print("\nRANDOM FOREST")
    print("-" * 80)

    print(f"MAE:  R$ {metrics.mae:,.2f}")
    print(f"RMSE: R$ {metrics.rmse:,.2f}")
    print(f"R²:   {metrics.r2:.4f}")

    print("\n" + "=" * 80)
    print("TREINAMENTO CONCLUÍDO")
    print("=" * 80)


if __name__ == "__main__":
    main()
