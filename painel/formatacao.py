"""Formatação de números e datas no padrão brasileiro."""
from __future__ import annotations

import pandas as pd

MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
VAZIO = "—"


def porcentagem(valor: float | None, casas: int = 1) -> str:
    if valor is None or pd.isna(valor):
        return VAZIO
    return f"{valor:.{casas}%}".replace(".", ",")


def numero(valor: float | None, casas: int = 0) -> str:
    if valor is None or pd.isna(valor):
        return VAZIO
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mes_ano(data: pd.Timestamp) -> str:
    """Ex.: 2019-06-10 -> 'jun/2019'."""
    return f"{MESES[data.month - 1]}/{data.year}"
