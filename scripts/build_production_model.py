from pi4_imoveis_sp.ml.production import (
    METADATA_FILE,
    MODEL_FILE,
    train_and_save_production_model,
)


def main() -> None:
    print("=" * 80)
    print("MODELO DE PRODUÇÃO — ITBI 2025")
    print("=" * 80)

    print("\nConfiguração congelada:")
    print("Algoritmo:       XGBoost")
    print("max_depth:       8")
    print("learning_rate:   0.05")
    print("n_estimators:    800")
    print("mes_transacao:   não utilizado")
    print("Dados:           janeiro a dezembro")

    print("\nTreinando modelo de produção...")

    _, metadata = train_and_save_production_model()

    print("\nTreinamento concluído.")

    print(f"Registros utilizados: {metadata['production_training_rows']:,}")

    print("\nArtefatos:")
    print(f"Modelo:    {MODEL_FILE}")
    print(f"Metadados: {METADATA_FILE}")

    print("\nMétricas oficiais preservadas (modelo de avaliação):")
    print(f"MAE:  R$ {metadata['official_evaluation']['metrics']['mae']:,.2f}")
    print(f"RMSE: R$ {metadata['official_evaluation']['metrics']['rmse']:,.2f}")
    print(f"R²:   {metadata['official_evaluation']['metrics']['r2']:.4f}")

    print("\n" + "=" * 80)
    print("MODELO DE PRODUÇÃO GERADO COM SUCESSO")
    print("=" * 80)


if __name__ == "__main__":
    main()
