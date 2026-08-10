from pi4_imoveis_sp.data.ingestion import (
    INTERIM_FILE,
    RAW_FILE,
    run_ingestion,
)


def main() -> None:
    print("=" * 80)
    print("INGESTÃO ITBI 2025")
    print("=" * 80)

    print(f"\nOrigem: {RAW_FILE}")
    print(f"Destino: {INTERIM_FILE}")

    dataframe = run_ingestion()

    print("\nIngestão concluída.")
    print(f"Registros: {dataframe.height:,}")
    print(f"Colunas: {dataframe.width}")

    print(f"Tamanho estimado em memória: {dataframe.estimated_size('mb'):.2f} MB")


if __name__ == "__main__":
    main()
