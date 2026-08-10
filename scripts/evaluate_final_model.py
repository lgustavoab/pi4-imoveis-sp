from pi4_imoveis_sp.ml.final_model import run_final_evaluation


def main() -> None:
    print("=" * 80)
    print("AVALIAÇÃO FINAL — XGBOOST ITBI 2025")
    print("=" * 80)

    print("\nModelo congelado:")
    print("max_depth:     8")
    print("learning_rate: 0.05")
    print("n_estimators:  800")
    print("mes_transacao: não utilizado como feature")

    print("\nTreinando em janeiro a novembro...")
    print("Avaliando no conjunto final de dezembro...")

    evaluation = run_final_evaluation()

    print("\nCONJUNTOS")
    print("-" * 80)

    print(f"Treino final: {evaluation.train_rows:,}")

    print(f"Teste final:  {evaluation.test_rows:,}")

    print("\nRESULTADO FINAL — DEZEMBRO")
    print("-" * 80)

    print(f"MAE:  R$ {evaluation.metrics.mae:,.2f}")

    print(f"RMSE: R$ {evaluation.metrics.rmse:,.2f}")

    print(f"R²:   {evaluation.metrics.r2:.4f}")

    print("\n" + "=" * 80)
    print("AVALIAÇÃO FINAL CONCLUÍDA")
    print("=" * 80)


if __name__ == "__main__":
    main()
