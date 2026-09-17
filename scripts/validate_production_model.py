import math
from importlib.metadata import version
from platform import python_version

from pi4_imoveis_sp.ml.dataset import (
    CATEGORICAL_FEATURES,
    FEATURE_COLUMNS_WITHOUT_MONTH,
    NUMERICAL_FEATURES_WITHOUT_MONTH,
    build_model_dataset,
)
from pi4_imoveis_sp.ml.inference import (
    load_model_metadata,
    load_production_model,
    predict_apartment_price,
)
from pi4_imoveis_sp.ml.production import (
    EXPECTED_PRODUCTION_ROWS,
    FINAL_HYPERPARAMETERS,
    FINAL_METRICS,
)


def main() -> None:
    print("=" * 80)
    print("VALIDAÇÃO DO MODELO DE PRODUÇÃO")
    print("=" * 80)

    print("\n1. CARREGANDO ARTEFATOS")
    print("-" * 80)

    model = load_production_model()
    metadata = load_model_metadata()

    print("Modelo carregado com sucesso.")
    print("Metadados carregados com sucesso.")

    print("\n2. VALIDANDO METADADOS")
    print("-" * 80)

    metadata_features = tuple(metadata["features"])

    if metadata_features != FEATURE_COLUMNS_WITHOUT_MONTH:
        raise ValueError(
            "As features registradas nos metadados não correspondem ao contrato atual."
        )

    if metadata["production_training_rows"] != EXPECTED_PRODUCTION_ROWS:
        raise ValueError(
            "Quantidade de registros de treinamento inesperada nos metadados."
        )

    if metadata["production_training"]["internal_holdout"] is not False:
        raise ValueError("O metadata descreve incorretamente um holdout de produção.")

    if tuple(metadata["categorical_features"]) != CATEGORICAL_FEATURES:
        raise ValueError("Contrato de features categóricas inválido.")

    if tuple(metadata["numerical_features"]) != NUMERICAL_FEATURES_WITHOUT_MONTH:
        raise ValueError("Contrato de features numéricas inválido.")

    if metadata["model"]["hyperparameters"] != FINAL_HYPERPARAMETERS:
        raise ValueError("Hiperparâmetros registrados divergem do modelo congelado.")

    official_evaluation = metadata["official_evaluation"]

    if official_evaluation["train_rows"] != 57_709:
        raise ValueError("Quantidade de treino da avaliação oficial inválida.")

    if official_evaluation["test_rows"] != 5_431:
        raise ValueError("Quantidade de teste da avaliação oficial inválida.")

    if official_evaluation["metrics"] != FINAL_METRICS:
        raise ValueError("Métricas oficiais registradas incorretamente.")

    expected_environment = {
        "python": python_version(),
        "scikit_learn": version("scikit-learn"),
        "xgboost": version("xgboost"),
        "pandas": version("pandas"),
        "polars": version("polars"),
        "joblib": version("joblib"),
    }

    if metadata["environment"] != expected_environment:
        raise ValueError("Versões do ambiente registradas incorretamente.")

    if metadata["project"]["version"] != version("pi4-imoveis-sp"):
        raise ValueError("Versão do projeto registrada incorretamente.")

    model_parameters = model.named_steps["model"].get_params()

    if any(
        model_parameters[name] != value for name, value in FINAL_HYPERPARAMETERS.items()
    ):
        raise ValueError("O modelo carregado diverge dos hiperparâmetros congelados.")

    print(f"Versão do modelo: {metadata['model_version']}")

    print(f"Registros de treinamento: {metadata['production_training_rows']:,}")

    print("Contrato de features válido.")
    print("Hiperparâmetros do Pipeline válidos.")
    print("Versões do ambiente válidas.")

    print("\n3. TESTE DE PREDIÇÃO")
    print("-" * 80)

    dataframe = build_model_dataset(
        exclude_severe_anomalies=True,
        include_month=False,
    )

    if dataframe.height != EXPECTED_PRODUCTION_ROWS:
        raise ValueError("Quantidade inesperada no dataset real de produção.")

    sample = dataframe.row(
        0,
        named=True,
    )

    prediction = predict_apartment_price(
        area=sample["Área Construída (m2)"],
        cep4=sample["cep4"],
        iptu_pattern=sample["Padrão (IPTU)"],
        property_age=sample["idade_imovel"],
        ideal_fraction=sample["Fração Ideal"],
        model=model,
    )

    if not math.isfinite(prediction):
        raise ValueError("O modelo produziu uma previsão não finita.")

    if prediction <= 0:
        raise ValueError("O modelo produziu uma previsão menor ou igual a zero.")

    if not isinstance(prediction, float):
        raise TypeError("A inferência não retornou float.")

    print(f"Área:          {sample['Área Construída (m2)']} m²")

    print(f"CEP4:          {sample['cep4']}")

    print(f"Padrão IPTU:   {sample['Padrão (IPTU)']}")

    print(f"Idade:         {sample['idade_imovel']} anos")

    print(f"Fração ideal:  {sample['Fração Ideal']}")

    print(
        f"\nValor real:    "
        f"R$ {sample['Valor de Transação (declarado pelo contribuinte)']:,.2f}"
    )

    print(f"Valor previsto: R$ {prediction:,.2f}")

    print(
        "\nObservação: esta previsão verifica apenas o funcionamento do artefato; "
        "não é uma métrica de generalização."
    )

    print("\n" + "=" * 80)
    print("MODELO DE PRODUÇÃO VALIDADO COM SUCESSO")
    print("=" * 80)


if __name__ == "__main__":
    main()
