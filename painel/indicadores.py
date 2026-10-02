"""Indicadores e recortes calculados sobre a base preparada."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from painel.dados import STATUS_CANCELADO

FAIXAS_IDADE = [-1, 7, 30, 90, 365, float("inf")]
ROTULOS_IDADE = ["Até 7 dias", "8 a 30 dias", "31 a 90 dias", "91 dias a 1 ano", "Mais de 1 ano"]
PADRAO_SERVICO_GENERICO = r"^99 |outr"


@dataclass(frozen=True)
class Indicadores:
    total: int
    backlog: int
    taxa_resolucao: float | None
    taxa_resolucao_bruta: float | None
    taxa_fechamento_auto: float | None
    nota_media: float | None
    adesao_avaliacao: float | None


def _razao(parte: int, todo: int) -> float | None:
    return parte / todo if todo else None


def calcular_indicadores(df: pd.DataFrame) -> Indicadores:
    total = len(df)
    cancelados = int(df["status"].eq(STATUS_CANCELADO).sum())
    resolvidos = int(df["resolvido"].sum())
    avaliados = df["nota_avaliacao"].notna()

    return Indicadores(
        total=total,
        backlog=int(df["pendente"].sum()),
        taxa_resolucao=_razao(resolvidos, total - cancelados),
        taxa_resolucao_bruta=_razao(resolvidos, total),
        taxa_fechamento_auto=_razao(int((df["auto"] & df["resolvido"]).sum()), resolvidos),
        nota_media=float(df.loc[avaliados, "nota_avaliacao"].mean()) if avaliados.any() else None,
        adesao_avaliacao=_razao(int(avaliados.sum()), resolvidos),
    )


def parcela_servicos_genericos(df: pd.DataFrame) -> float:
    """Fração dos chamados abertos em serviços do tipo "99 Outros…" ou "Outros"."""
    return float(df["servico"].str.contains(PADRAO_SERVICO_GENERICO, case=False, na=False).mean())


def pendentes_por_idade(df: pd.DataFrame, data_referencia: pd.Timestamp) -> pd.DataFrame:
    """Chamados pendentes com a idade em dias e a faixa de idade."""
    pendentes = df[df["pendente"]]
    idade = (data_referencia - pendentes["data_abertura"]).dt.days
    return pendentes.assign(
        idade=idade,
        faixa=pd.cut(idade, FAIXAS_IDADE, labels=ROTULOS_IDADE),
    )
