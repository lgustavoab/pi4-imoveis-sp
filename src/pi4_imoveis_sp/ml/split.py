from dataclasses import dataclass

import polars as pl

from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS,
    FEATURE_COLUMNS_WITHOUT_MONTH,
    TARGET_COLUMN,
    build_model_dataset,
)

TRAIN_END_MONTH = 10
VALIDATION_MONTH = 11
TEST_MONTH = 12


@dataclass(frozen=True)
class DatasetSplit:
    x_train: pl.DataFrame
    y_train: pl.Series
    x_validation: pl.DataFrame
    y_validation: pl.Series
    x_test: pl.DataFrame
    y_test: pl.Series


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

    train = dataframe.filter(pl.col("mes_transacao") <= TRAIN_END_MONTH)

    validation = dataframe.filter(pl.col("mes_transacao") == VALIDATION_MONTH)

    test = dataframe.filter(pl.col("mes_transacao") == TEST_MONTH)

    if train.height == 0:
        raise ValueError("O conjunto de treino está vazio.")

    if validation.height == 0:
        raise ValueError("O conjunto de validação está vazio.")

    if test.height == 0:
        raise ValueError("O conjunto de teste está vazio.")

    total_rows = train.height + validation.height + test.height

    if total_rows != dataframe.height:
        raise ValueError(
            "O split temporal não preservou todos os registros. "
            f"Split: {total_rows:,}. "
            f"Dataset: {dataframe.height:,}."
        )

    x_train, y_train = split_features_target(
        train,
        feature_columns,
    )

    x_validation, y_validation = split_features_target(
        validation,
        feature_columns,
    )

    x_test, y_test = split_features_target(
        test,
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
