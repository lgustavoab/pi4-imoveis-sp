from pathlib import Path

import polars as pl

from pi4_imoveis_sp.data.ingestion import (
    INTERIM_FILE,
    PROJECT_ROOT,
)

PROCESSED_FILE = PROJECT_ROOT / "data" / "processed" / "apartments_2025.parquet"

PURCHASE_AND_SALE = "1.Compra e venda"
APARTMENT_USE_CODE = 20
FULL_TRANSFER_PERCENTAGE = 100.0

VALUE_COLUMN = "Valor de Transação (declarado pelo contribuinte)"
VVR_COLUMN = "Valor Venal de Referência (proporcional)"
AREA_COLUMN = "Área Construída (m2)"
ACC_COLUMN = "ACC (IPTU)"


def validate_interim_file(
    path: Path = INTERIM_FILE,
) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Parquet intermediário não encontrado: {path}")


def load_interim_data(
    path: Path = INTERIM_FILE,
) -> pl.DataFrame:
    validate_interim_file(path)

    return pl.read_parquet(path)


def filter_apartment_sales(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    return dataframe.filter(
        (pl.col("Natureza de Transação") == PURCHASE_AND_SALE)
        & (pl.col("Uso (IPTU)") == APARTMENT_USE_CODE)
        & (
            (pl.col("Proporção Transmitida (%)") - FULL_TRANSFER_PERCENTAGE).abs()
            < 1e-9
        )
    )


def add_derived_features(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    return dataframe.with_columns(
        pl.col("CEP").cast(pl.String).str.pad_start(8, "0").alias("cep_normalizado"),
        (pl.lit(2025) - pl.col(ACC_COLUMN)).alias("idade_imovel"),
        (pl.col(VALUE_COLUMN) / pl.col(AREA_COLUMN)).alias("valor_m2"),
        (pl.col(VALUE_COLUMN) / pl.col(VVR_COLUMN)).alias("razao_transacao_vvr"),
    ).with_columns(
        pl.col("cep_normalizado").str.slice(0, 4).alias("cep4"),
    )


def add_quality_flags(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    return dataframe.with_columns(
        (pl.col("valor_m2") < 100).alias("flag_valor_m2_muito_baixo"),
        (pl.col("razao_transacao_vvr") < 0.10).alias("flag_transacao_muito_abaixo_vvr"),
    )


def validate_processed_data(
    dataframe: pl.DataFrame,
) -> None:
    if dataframe.height != 64_951:
        raise ValueError(
            "Quantidade inesperada de apartamentos processados: "
            f"{dataframe.height:,}. Esperado: 64.951."
        )

    required_columns = (
        VALUE_COLUMN,
        AREA_COLUMN,
        ACC_COLUMN,
        "cep_normalizado",
        "cep4",
        "idade_imovel",
        "valor_m2",
        "razao_transacao_vvr",
        "flag_valor_m2_muito_baixo",
        "flag_transacao_muito_abaixo_vvr",
    )

    missing_columns = [
        column for column in required_columns if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(f"Colunas processadas ausentes: {missing_columns}")

    invalid_cep = dataframe.filter(
        pl.col("cep_normalizado").str.len_chars() != 8
    ).height

    if invalid_cep:
        raise ValueError(
            f"Foram encontrados {invalid_cep} CEPs fora do formato de 8 dígitos."
        )

    invalid_age = dataframe.filter(
        (pl.col("idade_imovel") < 0) | pl.col("idade_imovel").is_null()
    ).height

    if invalid_age:
        raise ValueError(f"Foram encontradas {invalid_age} idades inválidas.")


def build_processed_dataframe(
    path: Path = INTERIM_FILE,
) -> pl.DataFrame:
    dataframe = load_interim_data(path)

    dataframe = filter_apartment_sales(dataframe)
    dataframe = add_derived_features(dataframe)
    dataframe = add_quality_flags(dataframe)

    validate_processed_data(dataframe)

    return dataframe


def write_processed_parquet(
    dataframe: pl.DataFrame,
    output_path: Path = PROCESSED_FILE,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.write_parquet(
        output_path,
        compression="zstd",
    )


def run_cleaning(
    source_path: Path = INTERIM_FILE,
    output_path: Path = PROCESSED_FILE,
) -> pl.DataFrame:
    dataframe = build_processed_dataframe(source_path)

    write_processed_parquet(
        dataframe,
        output_path,
    )

    return dataframe
