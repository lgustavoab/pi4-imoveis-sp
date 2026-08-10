import math

from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS_WITHOUT_MONTH,
    build_model_dataset,
)
from pi4_imoveis_sp.ml.inference import (
    load_model_metadata,
    load_production_model,
    predict_apartment_price,
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

    if metadata["training_rows"] != 63_807:
        raise ValueError(
            "Quantidade de registros de treinamento inesperada nos metadados."
        )

    print(f"Versão do modelo: {metadata['model_version']}")

    print(f"Registros de treinamento: {metadata['training_rows']:,}")

    print("Contrato de features válido.")

    print("\n3. TESTE DE PREDIÇÃO")
    print("-" * 80)

    dataframe = build_model_dataset(
        exclude_severe_anomalies=True,
        include_month=False,
    )

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

    print("\n" + "=" * 80)
    print("MODELO DE PRODUÇÃO VALIDADO COM SUCESSO")
    print("=" * 80)


if __name__ == "__main__":
    main()
