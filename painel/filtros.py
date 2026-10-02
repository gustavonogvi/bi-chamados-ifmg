"""Filtros da barra lateral."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class Filtros:
    ano_inicio: int
    ano_fim: int
    areas: tuple[str, ...] = ()
    campi: tuple[str, ...] = ()
    tipos: tuple[str, ...] = ()


def aplicar_filtros(df: pd.DataFrame, filtros: Filtros) -> pd.DataFrame:
    """Lista vazia num filtro significa "todos"."""
    mascara = df["data_abertura"].dt.year.between(filtros.ano_inicio, filtros.ano_fim)
    for coluna, valores in (("area", filtros.areas), ("campus", filtros.campi), ("tipo_servico", filtros.tipos)):
        if valores:
            mascara &= df[coluna].isin(valores)
    return df[mascara]


def _opcoes(df: pd.DataFrame, coluna: str) -> list[str]:
    return sorted(df[coluna].dropna().unique())


def escolher_filtros(base: pd.DataFrame) -> Filtros:
    """Desenha os filtros na barra lateral e devolve o que foi escolhido."""
    anos = sorted(int(ano) for ano in base["data_abertura"].dt.year.unique())
    with st.sidebar:
        st.subheader("Filtros")
        ano_inicio, ano_fim = st.select_slider("Período", options=anos, value=(anos[0], anos[-1]))
        areas = st.multiselect("Área", _opcoes(base, "area"), placeholder="Todas")
        campi = st.multiselect("Campus", _opcoes(base, "campus"), placeholder="Todos")
        tipos = st.multiselect("Tipo de serviço", _opcoes(base, "tipo_servico"), placeholder="Todos")
    return Filtros(ano_inicio, ano_fim, tuple(areas), tuple(campi), tuple(tipos))
