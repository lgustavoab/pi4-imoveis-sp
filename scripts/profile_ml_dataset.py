import polars as pl

from pi4_imoveis_sp.ml.dataset import build_model_dataset


def main() -> None:
    print("=" * 80)
    print("PERFIL DO DATASET DE MACHINE LEARNING")
    print("=" * 80)

    full_dataset = build_model_dataset(exclude_severe_anomalies=False)

    clean_dataset = build_model_dataset(exclude_severe_anomalies=True)

    print("\n1. TAMANHO DOS DATASETS")
    print("-" * 80)

    print(f"Dataset completo: {full_dataset.height:,}")

    print(f"Dataset principal: {clean_dataset.height:,}")

    removed = full_dataset.height - clean_dataset.height

    print(f"Registros removidos: {removed:,}")

    print("\n2. DISTRIBUIÇÃO MENSAL — DATASET PRINCIPAL")
    print("-" * 80)

    monthly_counts = clean_dataset.group_by("mes_transacao").len().sort("mes_transacao")

    print(monthly_counts)

    print("\n3. DISTRIBUIÇÃO PERCENTUAL")
    print("-" * 80)

    monthly_distribution = monthly_counts.with_columns(
        (pl.col("len") / clean_dataset.height * 100).round(2).alias("percentual")
    )

    print(monthly_distribution)

    print("\n4. FLAGS — DATASET COMPLETO")
    print("-" * 80)

    both_flags = full_dataset.filter(
        pl.col("flag_valor_m2_muito_baixo") & pl.col("flag_transacao_muito_abaixo_vvr")
    ).height

    only_low_m2 = full_dataset.filter(
        pl.col("flag_valor_m2_muito_baixo") & ~pl.col("flag_transacao_muito_abaixo_vvr")
    ).height

    only_low_vvr = full_dataset.filter(
        ~pl.col("flag_valor_m2_muito_baixo") & pl.col("flag_transacao_muito_abaixo_vvr")
    ).height

    print(f"Somente preço/m² muito baixo: {only_low_m2:,}")

    print(f"Somente transação muito abaixo do VVR: {only_low_vvr:,}")

    print(f"As duas flags simultaneamente: {both_flags:,}")

    print("\n" + "=" * 80)
    print("PERFIL CONCLUÍDO")
    print("=" * 80)


if __name__ == "__main__":
    main()
