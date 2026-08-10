import numpy as np
import polars as pl

from pi4_imoveis_sp.ml.dataset import TARGET_COLUMN
from pi4_imoveis_sp.ml.final_model import run_final_evaluation


def main() -> None:
    print("=" * 80)
    print("ANÁLISE DOS ERROS FINAIS — DEZEMBRO")
    print("=" * 80)

    evaluation = run_final_evaluation()

    dataframe = evaluation.test_data.with_columns(
        pl.Series(
            "predicao",
            evaluation.predictions,
        )
    )

    dataframe = dataframe.with_columns(
        (pl.col(TARGET_COLUMN) - pl.col("predicao")).alias("erro"),
        (pl.col(TARGET_COLUMN) - pl.col("predicao")).abs().alias("erro_absoluto"),
    )

    print("\n1. DISTRIBUIÇÃO DO VALOR REAL")
    print("-" * 80)

    quantiles = (
        0.50,
        0.75,
        0.90,
        0.95,
        0.99,
        0.995,
        0.999,
    )

    for quantile in quantiles:
        value = dataframe.select(pl.col(TARGET_COLUMN).quantile(quantile)).item()

        print(f"P{quantile * 100:>5.1f}: R$ {value:,.2f}")

    print("\n2. DISTRIBUIÇÃO DO ERRO ABSOLUTO")
    print("-" * 80)

    for quantile in quantiles:
        value = dataframe.select(pl.col("erro_absoluto").quantile(quantile)).item()

        print(f"P{quantile * 100:>5.1f}: R$ {value:,.2f}")

    print("\n3. ERRO POR FAIXA DE PREÇO")
    print("-" * 80)

    dataframe = dataframe.with_columns(
        pl.when(pl.col(TARGET_COLUMN) < 300_000)
        .then(pl.lit("< 300 mil"))
        .when(pl.col(TARGET_COLUMN) < 500_000)
        .then(pl.lit("300–500 mil"))
        .when(pl.col(TARGET_COLUMN) < 1_000_000)
        .then(pl.lit("500 mil–1 mi"))
        .when(pl.col(TARGET_COLUMN) < 2_000_000)
        .then(pl.lit("1–2 mi"))
        .when(pl.col(TARGET_COLUMN) < 5_000_000)
        .then(pl.lit("2–5 mi"))
        .otherwise(pl.lit(">= 5 mi"))
        .alias("faixa_preco")
    )

    price_groups = (
        dataframe.group_by("faixa_preco")
        .agg(
            pl.len().alias("registros"),
            pl.col("erro_absoluto").mean().alias("mae"),
        )
        .sort("mae")
    )

    print(price_groups)

    print("\n4. ERRO POR PADRÃO IPTU")
    print("-" * 80)

    pattern_groups = (
        dataframe.group_by("Padrão (IPTU)")
        .agg(
            pl.len().alias("registros"),
            pl.col("erro_absoluto").mean().alias("mae"),
        )
        .sort("mae", descending=True)
    )

    print(pattern_groups)

    print("\n5. MAIORES ERROS")
    print("-" * 80)

    worst_errors = (
        dataframe.select(
            [
                "cep4",
                "Área Construída (m2)",
                "Padrão (IPTU)",
                "idade_imovel",
                "Fração Ideal",
                TARGET_COLUMN,
                "predicao",
                "erro_absoluto",
            ]
        )
        .sort(
            "erro_absoluto",
            descending=True,
        )
        .head(20)
    )

    print(worst_errors)

    print("\n6. ERRO MÉDIO E MEDIANO")
    print("-" * 80)

    mean_error = np.mean(np.abs(evaluation.y_test - evaluation.predictions))

    median_error = np.median(np.abs(evaluation.y_test - evaluation.predictions))

    print(f"Erro absoluto médio:   R$ {mean_error:,.2f}")
    print(f"Erro absoluto mediano: R$ {median_error:,.2f}")

    print("\n" + "=" * 80)
    print("ANÁLISE FINAL CONCLUÍDA")
    print("=" * 80)


if __name__ == "__main__":
    main()
