from dataclasses import dataclass
from datetime import date

import polars as pl

from pi4_imoveis_sp.data.cleaning import (
    TRANSACTION_DATE_COLUMN,
    TRANSACTION_YEAR,
)
from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS,
    FEATURE_COLUMNS_WITHOUT_MONTH,
    TARGET_COLUMN,
    build_model_dataset,
)

SCOPE_START = date(TRANSACTION_YEAR, 1, 1)
VALIDATION_START = date(TRANSACTION_YEAR, 11, 1)
TEST_START = date(TRANSACTION_YEAR, 12, 1)
SCOPE_END = date(TRANSACTION_YEAR + 1, 1, 1)


@dataclass(frozen=True)
class TemporalPartitions:
    train: pl.DataFrame
    validation: pl.DataFrame
    test: pl.DataFrame


@dataclass(frozen=True)
class DatasetSplit:
    x_train: pl.DataFrame
    y_train: pl.Series
    x_validation: pl.DataFrame
    y_validation: pl.Series
    x_test: pl.DataFrame
    y_test: pl.Series


def date_range_condition(
    start: date,
    end: date,
) -> pl.Expr:
    return (pl.col(TRANSACTION_DATE_COLUMN) >= start) & (
        pl.col(TRANSACTION_DATE_COLUMN) < end
    )


def validate_temporal_partitions(
    dataframe: pl.DataFrame,
    partitions: TemporalPartitions,
) -> None:
    named_partitions = (
        ("treino", partitions.train, SCOPE_START, VALIDATION_START),
        ("validação", partitions.validation, VALIDATION_START, TEST_START),
        ("teste", partitions.test, TEST_START, SCOPE_END),
    )

    null_dates = dataframe.filter(pl.col(TRANSACTION_DATE_COLUMN).is_null()).height

    if null_dates:
        raise ValueError("O dataset do split contém datas de transação nulas.")

    outside_scope = dataframe.filter(
        ~date_range_condition(SCOPE_START, SCOPE_END)
    ).height

    if outside_scope:
        raise ValueError(
            f"O dataset do split contém {outside_scope} registros fora de "
            f"{TRANSACTION_YEAR}."
        )

    for name, partition, start, end in named_partitions:
        if partition.height == 0:
            raise ValueError(f"O conjunto de {name} está vazio.")

        invalid_dates = partition.filter(~date_range_condition(start, end)).height

        if invalid_dates:
            raise ValueError(
                f"O conjunto de {name} contém {invalid_dates} datas fora do intervalo."
            )

    partition_memberships = pl.sum_horizontal(
        date_range_condition(SCOPE_START, VALIDATION_START).cast(pl.Int8),
        date_range_condition(VALIDATION_START, TEST_START).cast(pl.Int8),
        date_range_condition(TEST_START, SCOPE_END).cast(pl.Int8),
    )

    invalid_memberships = dataframe.filter(partition_memberships != 1).height

    if invalid_memberships:
        raise ValueError(
            "Cada registro deve pertencer a exatamente um conjunto temporal. "
            f"Registros inválidos: {invalid_memberships:,}."
        )

    total_rows = (
        partitions.train.height + partitions.validation.height + partitions.test.height
    )

    if total_rows != dataframe.height:
        raise ValueError(
            "O split temporal não preservou todos os registros. "
            f"Split: {total_rows:,}. Dataset: {dataframe.height:,}."
        )

    train_max = partitions.train.get_column(TRANSACTION_DATE_COLUMN).max()
    validation_min = partitions.validation.get_column(TRANSACTION_DATE_COLUMN).min()
    validation_max = partitions.validation.get_column(TRANSACTION_DATE_COLUMN).max()
    test_min = partitions.test.get_column(TRANSACTION_DATE_COLUMN).min()

    if not train_max < validation_min <= validation_max < test_min:
        raise ValueError("A ordem cronológica dos conjuntos não foi preservada.")


def build_temporal_partitions(
    dataframe: pl.DataFrame,
) -> TemporalPartitions:
    partitions = TemporalPartitions(
        train=dataframe.filter(date_range_condition(SCOPE_START, VALIDATION_START)),
        validation=dataframe.filter(date_range_condition(VALIDATION_START, TEST_START)),
        test=dataframe.filter(date_range_condition(TEST_START, SCOPE_END)),
    )

    validate_temporal_partitions(dataframe, partitions)

    return partitions


def split_features_target(
    dataframe: pl.DataFrame,
    feature_columns: tuple[str, ...],
) -> tuple[pl.DataFrame, pl.Series]:
    features = dataframe.select(feature_columns)
    target = dataframe.get_column(TARGET_COLUMN)

    return features, target


def build_temporal_split(
    include_month: bool = True,
) -> DatasetSplit:
    dataframe = build_model_dataset(
        exclude_severe_anomalies=True,
        include_month=include_month,
    )

    feature_columns = (
        FEATURE_COLUMNS if include_month else FEATURE_COLUMNS_WITHOUT_MONTH
    )

    partitions = build_temporal_partitions(dataframe)

    x_train, y_train = split_features_target(
        partitions.train,
        feature_columns,
    )

    x_validation, y_validation = split_features_target(
        partitions.validation,
        feature_columns,
    )

    x_test, y_test = split_features_target(
        partitions.test,
        feature_columns,
    )

    return DatasetSplit(
        x_train=x_train,
        y_train=y_train,
        x_validation=x_validation,
        y_validation=y_validation,
        x_test=x_test,
        y_test=y_test,
    )
