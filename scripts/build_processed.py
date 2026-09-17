from pi4_imoveis_sp.data.cleaning import (
    PROCESSED_FILE,
    run_cleaning,
)
from pi4_imoveis_sp.data.ingestion import INTERIM_FILE


def main() -> None:
    print("=" * 80)
    print("PROCESSAMENTO DOS APARTAMENTOS — ITBI 2025")
    print("=" * 80)

    print(f"\nOrigem: {INTERIM_FILE}")
    print(f"Destino: {PROCESSED_FILE}")
    print("Escopo: Data de Transação restrita ao ano de 2025.")

    dataframe = run_cleaning()

    print("\nProcessamento concluído.")
    print(f"Registros: {dataframe.height:,}")
    print(f"Colunas: {dataframe.width}")

    print("\nFlags de qualidade:")

    low_value_m2 = dataframe.filter(dataframe["flag_valor_m2_muito_baixo"]).height

    low_transaction_vvr = dataframe.filter(
        dataframe["flag_transacao_muito_abaixo_vvr"]
    ).height

    print(f"Valor abaixo de R$ 100/m²: {low_value_m2:,}")

    print(f"Transação abaixo de 10% do VVR: {low_transaction_vvr:,}")

    print(f"\nTamanho estimado em memória: {dataframe.estimated_size('mb'):.2f} MB")


if __name__ == "__main__":
    main()
