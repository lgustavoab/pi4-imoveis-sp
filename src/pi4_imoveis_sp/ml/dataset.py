import polars as pl

from pi4_imoveis_sp.data.cleaning import (
    AREA_COLUMN,
    PROCESSED_FILE,
    TRANSACTION_DATE_COLUMN,
    TRANSACTION_YEAR,
    VALUE_COLUMN,
)

TARGET_COLUMN = VALUE_COLUMN

FEATURE_COLUMNS = (
    AREA_COLUMN,
    "cep4",
    "Padrão (IPTU)",
    "idade_imovel",
    "Fração Ideal",
    "mes_transacao",
)

FEATURE_COLUMNS_WITHOUT_MONTH = (
    AREA_COLUMN,
    "cep4",
    "Padrão (IPTU)",
    "idade_imovel",
    "Fração Ideal",
)

CATEGORICAL_FEATURES = (
    "cep4",
    "Padrão (IPTU)",
)

NUMERICAL_FEATURES = (
    AREA_COLUMN,
    "idade_imovel",
    "Fração Ideal",
    "mes_transacao",
)

NUMERICAL_FEATURES_WITHOUT_MONTH = (
    AREA_COLUMN,
    "idade_imovel",
    "Fração Ideal",
)

QUALITY_FLAG_COLUMNS = (
    "flag_valor_m2_muito_baixo",
    "flag_transacao_muito_abaixo_vvr",
)

LEAKAGE_COLUMNS = (
    "Valor Venal de Referência",
    "Valor Venal de Referência (proporcional)",
    "Base de Cálculo adotada",
    "Valor Financiado",
    "valor_m2",
    "razao_transacao_vvr",
)


def load_processed_dataset() -> pl.DataFrame:
    if not PROCESSED_FILE.exists():
        raise FileNotFoundError(f"Dataset processado não encontrado: {PROCESSED_FILE}")

    return pl.read_parquet(PROCESSED_FILE)


def add_transaction_month(
    dataframe: pl.DataFrame,
) -> pl.DataFrame:
    if "Data de Transação" not in dataframe.columns:
        raise ValueError("A coluna 'Data de Transação' não está presente no dataset.")

    return dataframe.with_columns(
        pl.col(TRANSACTION_DATE_COLUMN).dt.month().cast(pl.Int8).alias("mes_transacao")
    )


def validate_model_temporal_scope(
    dataframe: pl.DataFrame,
) -> None:
    if TRANSACTION_DATE_COLUMN not in dataframe.columns:
        raise ValueError(
            f"A coluna {TRANSACTION_DATE_COLUMN!r} não está presente no dataset."
        )

    null_dates = dataframe.filter(pl.col(TRANSACTION_DATE_COLUMN).is_null()).height

    if null_dates:
        raise ValueError("O dataset de ML contém datas de transação nulas.")

    outside_scope = dataframe.filter(
        pl.col(TRANSACTION_DATE_COLUMN).dt.year() != TRANSACTION_YEAR
    ).height

    if outside_scope:
        raise ValueError(
            f"O dataset de ML contém {outside_scope} registros fora de "
            f"{TRANSACTION_YEAR}."
        )


def validate_model_columns(
    dataframe: pl.DataFrame,
    feature_columns: tuple[str, ...] = FEATURE_COLUMNS,
) -> None:
    required_columns = (
        *feature_columns,
        TARGET_COLUMN,
        *QUALITY_FLAG_COLUMNS,
    )

    missing_columns = [
        column for column in required_columns if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(f"Colunas necessárias para ML ausentes: {missing_columns}")

    null_counts = dataframe.select(
        [
            pl.col(column).null_count().alias(column)
            for column in (
                *feature_columns,
                TARGET_COLUMN,
            )
        ]
    )

    columns_with_nulls = [
        column for column in null_counts.columns if null_counts[column][0] > 0
    ]

    if columns_with_nulls:
        raise ValueError(
            "Existem valores nulos nas colunas utilizadas pelo modelo: "
            f"{columns_with_nulls}"
        )


def build_model_dataset(
    exclude_severe_anomalies: bool = False,
    include_month: bool = True,
) -> pl.DataFrame:
    dataframe = load_processed_dataset()

    dataframe = add_transaction_month(dataframe)
    validate_model_temporal_scope(dataframe)

    feature_columns = (
        FEATURE_COLUMNS if include_month else FEATURE_COLUMNS_WITHOUT_MONTH
    )

    validate_model_columns(
        dataframe,
        feature_columns,
    )

    if exclude_severe_anomalies:
        dataframe = dataframe.filter(
            ~pl.col("flag_valor_m2_muito_baixo")
            & ~pl.col("flag_transacao_muito_abaixo_vvr")
        )

    selected_columns = (
        *feature_columns,
        TARGET_COLUMN,
        *QUALITY_FLAG_COLUMNS,
        TRANSACTION_DATE_COLUMN,
    )

    if "mes_transacao" not in selected_columns:
        selected_columns = (
            *selected_columns,
            "mes_transacao",
        )

    return dataframe.select(selected_columns)
