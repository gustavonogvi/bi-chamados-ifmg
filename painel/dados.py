"""Leitura e preparação da base de chamados.

Nada aqui depende do Streamlit, então tudo pode ser testado direto com pandas.
"""
from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pandas as pd

STATUS_RESOLVIDO = frozenset({"Fechado", "Resolvido"})
STATUS_PENDENTE = frozenset({"Aberto", "Em atendimento", "Suspenso", "Reaberto"})
STATUS_CANCELADO = "Cancelado"

COLUNAS_OBRIGATORIAS = frozenset({
    "chamado_id", "data_abertura", "data_ultima_movimentacao",
    "area", "grupo_servico", "servico", "tipo_servico", "campus",
    "status", "meio_abertura", "fechado_automaticamente", "nota_avaliacao",
})
COLUNAS_DATA = ("data_abertura", "data_ultima_movimentacao")
COLUNAS_TEXTO = ("area", "grupo_servico", "servico", "tipo_servico", "campus", "status", "meio_abertura")


class BaseInvalidaError(ValueError):
    """A base não tem o formato esperado."""


def preparar(bruto: pd.DataFrame) -> pd.DataFrame:
    """Valida as colunas e acrescenta os campos derivados usados no painel."""
    faltando = COLUNAS_OBRIGATORIAS - set(bruto.columns)
    if faltando:
        raise BaseInvalidaError(f"Faltam colunas na base: {', '.join(sorted(faltando))}.")

    datas = {col: pd.to_datetime(bruto[col], errors="coerce") for col in COLUNAS_DATA}
    textos = {col: bruto[col].astype("string").str.strip() for col in COLUNAS_TEXTO}
    df = bruto.assign(**datas, **textos).dropna(subset=["data_abertura"])

    return df.assign(
        # Na base, "Y" quer dizer sim e o campo vazio quer dizer não.
        auto=df["fechado_automaticamente"].astype("string").str.upper().eq("Y").fillna(False).astype(bool),
        nota_avaliacao=pd.to_numeric(df["nota_avaliacao"], errors="coerce"),
        resolvido=df["status"].isin(STATUS_RESOLVIDO).astype(bool),
        pendente=df["status"].isin(STATUS_PENDENTE).astype(bool),
        mes=df["data_abertura"].dt.to_period("M").dt.to_timestamp(),
        # A base não traz a data de fechamento; a última movimentação é a melhor aproximação.
        dias_ate_ult_mov=(df["data_ultima_movimentacao"] - df["data_abertura"]).dt.days,
    )


def ler_csv(origem: str | Path | BinaryIO) -> pd.DataFrame:
    """Lê o CSV de chamados (caminho ou arquivo enviado) e já devolve a base preparada."""
    return preparar(pd.read_csv(origem))
