import polars as pl

from pi4_imoveis_sp.data.cleaning import (
    ACC_COLUMN,
    APARTMENT_USE_CODE,
    AREA_COLUMN,
    EXPECTED_PROCESSED_ROWS,
    FULL_TRANSFER_PERCENTAGE,
    PROCESSED_FILE,
    PURCHASE_AND_SALE,
    TRANSACTION_DATE_COLUMN,
    TRANSACTION_YEAR,
    VALUE_COLUMN,
)

EXPECTED_ROWS = EXPECTED_PROCESSED_ROWS
EXPECTED_COLUMNS = 37
EXPECTED_LOW_VALUE_M2 = 1_018
EXPECTED_LOW_TRANSACTION_VVR = 301
EXPECTED_BOTH_FLAGS = 232
EXPECTED_FLAG_UNION = 1_087
EXPECTED_VALID_ROWS = 63_140


def main() -> None:
    print("=" * 80)
    print("VALIDAÇÃO DO DATASET PROCESSADO — ITBI 2025")
    print("=" * 80)
    print("\nData de Transação restrita ao ano de 2025.")

    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(f"Dataset processado não encontrado: {PROCESSED_FILE}")

    dataframe = pl.read_parquet(PROCESSED_FILE)

    print(f"\nArquivo: {PROCESSED_FILE}")
    print(f"Registros: {dataframe.height:,}")
    print(f"Colunas: {dataframe.width}")

    print("\n1. DIMENSÕES")
    print("-" * 80)

    if dataframe.height != EXPECTED_ROWS:
        raise ValueError(
            f"Quantidade inesperada de registros: "
            f"{dataframe.height:,}. Esperado: {EXPECTED_ROWS:,}."
        )

    if dataframe.width != EXPECTED_COLUMNS:
        raise ValueError(
            f"Quantidade inesperada de colunas: "
            f"{dataframe.width}. Esperado: {EXPECTED_COLUMNS}."
        )

    print("Dimensões válidas.")

    print("\n2. ESCOPO DO DATASET")
    print("-" * 80)

    invalid_nature = dataframe.filter(
        pl.col("Natureza de Transação") != PURCHASE_AND_SALE
    ).height

    invalid_use = dataframe.filter(pl.col("Uso (IPTU)") != APARTMENT_USE_CODE).height

    invalid_transfer = dataframe.filter(
        (pl.col("Proporção Transmitida (%)") - FULL_TRANSFER_PERCENTAGE).abs() >= 1e-9
    ).height

    null_transaction_dates = dataframe.filter(
        pl.col(TRANSACTION_DATE_COLUMN).is_null()
    ).height

    outside_transaction_year = dataframe.filter(
        pl.col(TRANSACTION_DATE_COLUMN).dt.year() != TRANSACTION_YEAR
    ).height

    minimum_date = dataframe.get_column(TRANSACTION_DATE_COLUMN).min()
    maximum_date = dataframe.get_column(TRANSACTION_DATE_COLUMN).max()

    print(f"Natureza inválida: {invalid_nature:,}")
    print(f"Uso IPTU inválido: {invalid_use:,}")
    print(f"Proporção transmitida inválida: {invalid_transfer:,}")
    print(f"Datas de transação nulas: {null_transaction_dates:,}")
    print(f"Datas fora de {TRANSACTION_YEAR}: {outside_transaction_year:,}")
    print(f"Data mínima: {minimum_date}")
    print(f"Data máxima: {maximum_date}")

    if (
        invalid_nature
        or invalid_use
        or invalid_transfer
        or null_transaction_dates
        or outside_transaction_year
    ):
        raise ValueError("O dataset contém registros fora do escopo definido.")

    if minimum_date.year != TRANSACTION_YEAR or maximum_date.year != TRANSACTION_YEAR:
        raise ValueError("Os limites temporais não pertencem ao ano de 2025.")

    print("\n3. FEATURES DERIVADAS")
    print("-" * 80)

    derived_columns = (
        "cep_normalizado",
        "cep4",
        "idade_imovel",
        "valor_m2",
        "razao_transacao_vvr",
        "flag_valor_m2_muito_baixo",
        "flag_transacao_muito_abaixo_vvr",
    )

    missing_columns = [
        column for column in derived_columns if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(f"Features derivadas ausentes: {missing_columns}")

    print("Features derivadas presentes.")

    print("\n4. CEP")
    print("-" * 80)

    invalid_cep = dataframe.filter(
        pl.col("cep_normalizado").is_null()
        | (pl.col("cep_normalizado").str.len_chars() != 8)
    ).height

    invalid_cep4 = dataframe.filter(
        pl.col("cep4").is_null() | (pl.col("cep4").str.len_chars() != 4)
    ).height

    distinct_cep4 = dataframe.select(pl.col("cep4").n_unique()).item()

    print(f"CEPs inválidos: {invalid_cep:,}")
    print(f"CEP4 inválidos: {invalid_cep4:,}")
    print(f"CEP4 distintos: {distinct_cep4:,}")

    if invalid_cep or invalid_cep4:
        raise ValueError("Foram encontrados CEPs derivados inválidos.")

    print("\n5. VARIÁVEIS NUMÉRICAS PRINCIPAIS")
    print("-" * 80)

    invalid_value = dataframe.filter(
        pl.col(VALUE_COLUMN).is_null() | (pl.col(VALUE_COLUMN) <= 0)
    ).height

    invalid_area = dataframe.filter(
        pl.col(AREA_COLUMN).is_null() | (pl.col(AREA_COLUMN) <= 0)
    ).height

    invalid_acc = dataframe.filter(
        pl.col(ACC_COLUMN).is_null() | (pl.col(ACC_COLUMN) > TRANSACTION_YEAR)
    ).height

    invalid_age = dataframe.filter(
        pl.col("idade_imovel").is_null() | (pl.col("idade_imovel") < 0)
    ).height

    invalid_fraction = dataframe.filter(
        pl.col("Fração Ideal").is_null()
        | (pl.col("Fração Ideal") <= 0)
        | (pl.col("Fração Ideal") > 1)
    ).height

    print(f"Valores de transação inválidos: {invalid_value:,}")
    print(f"Áreas inválidas: {invalid_area:,}")
    print(f"ACC inválidos: {invalid_acc:,}")
    print(f"Idades inválidas: {invalid_age:,}")
    print(f"Frações ideais inválidas: {invalid_fraction:,}")

    if invalid_value or invalid_area or invalid_acc or invalid_age or invalid_fraction:
        raise ValueError(
            "Foram encontrados valores inválidos nas variáveis principais."
        )

    print("\n6. FLAGS DE QUALIDADE")
    print("-" * 80)

    low_value_m2 = dataframe.filter(pl.col("flag_valor_m2_muito_baixo")).height

    low_transaction_vvr = dataframe.filter(
        pl.col("flag_transacao_muito_abaixo_vvr")
    ).height

    both_flags = dataframe.filter(
        pl.col("flag_valor_m2_muito_baixo") & pl.col("flag_transacao_muito_abaixo_vvr")
    ).height

    flag_union = dataframe.filter(
        pl.col("flag_valor_m2_muito_baixo") | pl.col("flag_transacao_muito_abaixo_vvr")
    ).height

    valid_rows = dataframe.height - flag_union

    print(f"Valor abaixo de R$ 100/m²: {low_value_m2:,}")

    print(f"Transação abaixo de 10% do VVR: {low_transaction_vvr:,}")
    print(f"Interseção das flags: {both_flags:,}")
    print(f"União das flags: {flag_union:,}")
    print(f"Registros economicamente válidos: {valid_rows:,}")

    if low_value_m2 != EXPECTED_LOW_VALUE_M2:
        raise ValueError("Quantidade inesperada para flag_valor_m2_muito_baixo.")

    if low_transaction_vvr != EXPECTED_LOW_TRANSACTION_VVR:
        raise ValueError("Quantidade inesperada para flag_transacao_muito_abaixo_vvr.")

    if both_flags != EXPECTED_BOTH_FLAGS:
        raise ValueError("Quantidade inesperada para a interseção das flags.")

    if flag_union != EXPECTED_FLAG_UNION:
        raise ValueError("Quantidade inesperada para a união das flags.")

    if valid_rows != EXPECTED_VALID_ROWS:
        raise ValueError("Quantidade inesperada de registros economicamente válidos.")

    print("\n7. INTERVALOS DE IDADE")
    print("-" * 80)

    age_summary = dataframe.select(
        pl.col("idade_imovel").min().alias("mínimo"),
        pl.col("idade_imovel").median().alias("mediana"),
        pl.col("idade_imovel").max().alias("máximo"),
    )

    print(age_summary)

    print("\n" + "=" * 80)
    print("DATASET PROCESSADO VALIDADO COM SUCESSO")
    print("=" * 80)


if __name__ == "__main__":
    main()
