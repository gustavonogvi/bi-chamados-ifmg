"""Painel de BI da Central de Serviços de TI do IFMG.

Para abrir:  streamlit run app.py   (ou dois cliques em rodar.bat)
A base padrão fica em dados/chamados-de-suporte.csv; outra pode ser enviada pela barra lateral.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from painel import abas
from painel import formatacao as fmt
from painel.dados import STATUS_PENDENTE, BaseInvalidaError, ler_csv
from painel.filtros import aplicar_filtros, escolher_filtros
from painel.indicadores import Indicadores, calcular_indicadores
from painel.tema import aplicar_tema

BASE_PADRAO = Path(__file__).parent / "dados" / "chamados-de-suporte.csv"


@st.cache_data(show_spinner="Carregando a base…")
def carregar(origem) -> pd.DataFrame:
    return ler_csv(origem)


def escolher_origem():
    with st.sidebar.expander("Base de dados"):
        enviado = st.file_uploader("Usar outro CSV", type="csv")
    if enviado is not None:
        return enviado
    return BASE_PADRAO if BASE_PADRAO.exists() else None


def mostrar_indicadores(ind: Indicadores) -> None:
    colunas = st.columns(6)
    cartoes = [
        ("Chamados", fmt.numero(ind.total), None),
        ("Resolução", fmt.porcentagem(ind.taxa_resolucao),
         "Fechados e resolvidos sobre o total, sem contar os cancelados. "
         f"Contando os cancelados: {fmt.porcentagem(ind.taxa_resolucao_bruta)}."),
        ("Automáticos", fmt.porcentagem(ind.taxa_fechamento_auto),
         "Parcela dos chamados resolvidos que o sistema fechou sozinho, sem confirmação do usuário."),
        ("Nota média", fmt.numero(ind.nota_media, 2),
         "Escala de 1 a 5, considerando só os chamados avaliados."),
        ("Avaliados", fmt.porcentagem(ind.adesao_avaliacao),
         "Parcela dos chamados resolvidos que receberam nota. Com poucos avaliados, a nota média diz pouco."),
        ("Pendentes", fmt.numero(ind.backlog),
         "Chamados com status " + ", ".join(sorted(STATUS_PENDENTE)) + "."),
    ]
    for coluna, (rotulo, valor, ajuda) in zip(colunas, cartoes):
        coluna.metric(rotulo, valor, help=ajuda, border=True)


def main() -> None:
    st.set_page_config(page_title="Central de Serviços de TI · IFMG", page_icon=":material/insights:",
                       layout="wide")
    aplicar_tema()

    origem = escolher_origem()
    if origem is None:
        st.info("Coloque o arquivo chamados-de-suporte.csv na pasta dados/ ou envie um CSV pela barra lateral.")
        st.stop()
    try:
        base = carregar(origem)
    except (BaseInvalidaError, pd.errors.ParserError, UnicodeDecodeError) as erro:
        st.error(f"Não consegui ler a base. {erro}")
        st.stop()

    inicio, fim = base["data_abertura"].min(), base["data_abertura"].max()
    st.title("Central de Serviços de TI")
    st.caption(f"IFMG · {fmt.numero(len(base))} chamados abertos entre {fmt.mes_ano(inicio)} e {fmt.mes_ano(fim)}")

    filtros = escolher_filtros(base)
    st.sidebar.caption(f"Dados até {fim:%d/%m/%Y}. O último ano pode estar incompleto.")

    df = aplicar_filtros(base, filtros)
    if df.empty:
        st.warning("Nenhum chamado atende aos filtros escolhidos.")
        st.stop()

    mostrar_indicadores(calcular_indicadores(df))

    volume, servicos, campus, satisfacao, automacao, gargalos = st.tabs(
        ["Volume e status", "Serviços", "Campus e área", "Satisfação", "Automação", "Gargalos"]
    )
    with volume:
        abas.volume(df)
    with servicos:
        abas.servicos(df)
    with campus:
        abas.campus(df)
    with satisfacao:
        abas.satisfacao(df)
    with automacao:
        abas.automacao(df)
    with gargalos:
        abas.gargalos(df, fim)


main()
