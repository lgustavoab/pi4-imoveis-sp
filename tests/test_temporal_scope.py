from datetime import date

import polars as pl
import pytest

import pi4_imoveis_sp.ml.dataset as dataset_module
from pi4_imoveis_sp.data.cleaning import (
    AREA_COLUMN,
    TRANSACTION_DATE_COLUMN,
    filter_transaction_year,
)
from pi4_imoveis_sp.ml.dataset import (
    FEATURE_COLUMNS_WITHOUT_MONTH,
    TARGET_COLUMN,
    build_model_dataset,
)
from pi4_imoveis_sp.ml.split import build_temporal_partitions


def build_synthetic_model_dataframe() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "record_id": [1, 2, 3, 4, 5],
            TRANSACTION_DATE_COLUMN: [
                date(2025, 1, 1),
                date(2025, 10, 31),
                date(2025, 11, 1),
                date(2025, 11, 30),
                date(2025, 12, 31),
            ],
            AREA_COLUMN: [50.0, 60.0, 70.0, 80.0, 90.0],
            "cep4": ["0100", "0200", "0300", "0400", "0500"],
            "Padrão (IPTU)": [20, 21, 22, 23, 24],
            "idade_imovel": [5, 10, 15, 20, 25],
            "Fração Ideal": [0.01, 0.02, 0.03, 0.04, 0.05],
            TARGET_COLUMN: [
                200_000.0,
                300_000.0,
                400_000.0,
                500_000.0,
                600_000.0,
            ],
            "flag_valor_m2_muito_baixo": [False] * 5,
            "flag_transacao_muito_abaixo_vvr": [False] * 5,
        }
    )


def test_filter_transaction_year_keeps_only_2025() -> None:
    dataframe = pl.DataFrame(
        {
            TRANSACTION_DATE_COLUMN: [
                date(2024, 12, 31),
                date(2025, 1, 1),
                date(2025, 12, 31),
                date(2026, 1, 1),
                None,
            ]
        }
    )

    result = filter_transaction_year(dataframe)

    assert result.get_column(TRANSACTION_DATE_COLUMN).to_list() == [
        date(2025, 1, 1),
        date(2025, 12, 31),
    ]


def test_model_dataset_contains_only_2025(monkeypatch: pytest.MonkeyPatch) -> None:
    dataframe = build_synthetic_model_dataframe()

    monkeypatch.setattr(
        dataset_module,
        "load_processed_dataset",
        lambda: dataframe,
    )

    result = build_model_dataset(
        exclude_severe_anomalies=True,
        include_month=False,
    )

    assert result.get_column(TRANSACTION_DATE_COLUMN).dt.year().unique().to_list() == [
        2025
    ]
    assert tuple(result.select(FEATURE_COLUMNS_WITHOUT_MONTH).columns) == (
        FEATURE_COLUMNS_WITHOUT_MONTH
    )


def test_model_dataset_rejects_record_outside_2025(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataframe = build_synthetic_model_dataframe().with_columns(
        pl.when(pl.col("record_id") == 1)
        .then(date(2024, 12, 31))
        .otherwise(pl.col(TRANSACTION_DATE_COLUMN))
        .alias(TRANSACTION_DATE_COLUMN)
    )

    monkeypatch.setattr(
        dataset_module,
        "load_processed_dataset",
        lambda: dataframe,
    )

    with pytest.raises(ValueError, match="fora de 2025"):
        build_model_dataset(
            exclude_severe_anomalies=True,
            include_month=False,
        )


def test_temporal_partitions_use_expected_date_ranges() -> None:
    dataframe = build_synthetic_model_dataframe()

    partitions = build_temporal_partitions(dataframe)

    assert partitions.train.get_column("record_id").to_list() == [1, 2]
    assert partitions.validation.get_column("record_id").to_list() == [3, 4]
    assert partitions.test.get_column("record_id").to_list() == [5]

    assert partitions.train.get_column(TRANSACTION_DATE_COLUMN).max() < date(
        2025, 11, 1
    )
    assert partitions.validation.get_column(TRANSACTION_DATE_COLUMN).min() >= date(
        2025, 11, 1
    )
    assert partitions.validation.get_column(TRANSACTION_DATE_COLUMN).max() < date(
        2025, 12, 1
    )
    assert partitions.test.get_column(TRANSACTION_DATE_COLUMN).min() >= date(
        2025, 12, 1
    )


def test_temporal_partitions_are_disjoint_and_cover_dataset() -> None:
    dataframe = build_synthetic_model_dataframe()

    partitions = build_temporal_partitions(dataframe)

    train_ids = set(partitions.train.get_column("record_id"))
    validation_ids = set(partitions.validation.get_column("record_id"))
    test_ids = set(partitions.test.get_column("record_id"))

    assert train_ids.isdisjoint(validation_ids)
    assert train_ids.isdisjoint(test_ids)
    assert validation_ids.isdisjoint(test_ids)
    assert train_ids | validation_ids | test_ids == set(
        dataframe.get_column("record_id")
    )


def test_temporal_partitions_reject_record_outside_2025() -> None:
    dataframe = build_synthetic_model_dataframe().vstack(
        pl.DataFrame(
            {
                "record_id": [6],
                TRANSACTION_DATE_COLUMN: [date(2026, 1, 1)],
                AREA_COLUMN: [100.0],
                "cep4": ["0600"],
                "Padrão (IPTU)": [25],
                "idade_imovel": [30],
                "Fração Ideal": [0.06],
                TARGET_COLUMN: [700_000.0],
                "flag_valor_m2_muito_baixo": [False],
                "flag_transacao_muito_abaixo_vvr": [False],
            }
        )
    )

    with pytest.raises(ValueError, match="fora de 2025"):
        build_temporal_partitions(dataframe)
