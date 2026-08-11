from unittest.mock import MagicMock

import pandas as pd

from pi4_imoveis_sp.ml.inference import (
    predict_apartment_price,
)


def test_predict_apartment_price_returns_float() -> None:
    model = MagicMock()
    model.predict.return_value = [627_950.31]

    prediction = predict_apartment_price(
        area=117.0,
        cep4="0430",
        iptu_pattern=22,
        property_age=3,
        ideal_fraction=0.0037,
        model=model,
    )

    assert prediction == 627_950.31
    assert isinstance(prediction, float)


def test_predict_apartment_price_uses_expected_columns() -> None:
    model = MagicMock()
    model.predict.return_value = [500_000.0]

    predict_apartment_price(
        area=80.0,
        cep4="0453",
        iptu_pattern=22,
        property_age=15,
        ideal_fraction=0.0100,
        model=model,
    )

    input_dataframe = model.predict.call_args.args[0]

    assert isinstance(input_dataframe, pd.DataFrame)

    assert list(input_dataframe.columns) == [
        "Área Construída (m2)",
        "cep4",
        "Padrão (IPTU)",
        "idade_imovel",
        "Fração Ideal",
    ]


def test_predict_apartment_price_passes_correct_values() -> None:
    model = MagicMock()
    model.predict.return_value = [750_000.0]

    predict_apartment_price(
        area=100.0,
        cep4="0453",
        iptu_pattern=23,
        property_age=10,
        ideal_fraction=0.0125,
        model=model,
    )

    input_dataframe = model.predict.call_args.args[0]

    row = input_dataframe.iloc[0]

    assert row["Área Construída (m2)"] == 100.0
    assert row["cep4"] == "0453"
    assert row["Padrão (IPTU)"] == 23
    assert row["idade_imovel"] == 10
    assert row["Fração Ideal"] == 0.0125


def test_predict_apartment_price_calls_model_once() -> None:
    model = MagicMock()
    model.predict.return_value = [400_000.0]

    predict_apartment_price(
        area=60.0,
        cep4="0301",
        iptu_pattern=21,
        property_age=20,
        ideal_fraction=0.0050,
        model=model,
    )

    model.predict.assert_called_once()
