import polars as pl

from pi4_imoveis_sp.presentation import build_pattern_label


def normalize_cep(
    cep: str,
) -> str:
    return "".join(character for character in cep if character.isdigit())


def format_cep(
    cep: str,
) -> str:
    return f"{cep[:5]}-{cep[5:]}"


def get_pattern_options(
    dataframe: pl.DataFrame,
) -> dict[int, str]:
    patterns = (
        dataframe.select(
            [
                "Padrão (IPTU)",
                "Descrição do padrão (IPTU)",
            ]
        )
        .unique()
        .sort("Padrão (IPTU)")
    )

    options: dict[int, str] = {}

    for row in patterns.iter_rows(named=True):
        code = row["Padrão (IPTU)"]
        description = row["Descrição do padrão (IPTU)"]

        if code is None:
            continue

        options[code] = build_pattern_label(
            code=code,
            description=description,
        )

    return options
