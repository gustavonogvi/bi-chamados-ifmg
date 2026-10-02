"""Conteúdo de cada aba do painel."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from painel import formatacao as fmt
from painel.indicadores import parcela_servicos_genericos, pendentes_por_idade
from painel.tema import ROTULOS, cores_atuais

# Abaixo destes volumes a média fica instável demais para comparar grupos.
MIN_AVALIACOES_POR_AREA = 20
MIN_RESOLVIDOS_POR_AREA = 50
MIN_CHAMADOS_POR_GRUPO = 30
ALTURA_POR_BARRA = 28


def _grafico(fig) -> None:
    # O título sai do gráfico e vira texto acima dele: o tema do Streamlit põe a legenda
    # no topo e ela ficaria por cima do título. Assim também combina com os títulos das tabelas.
    titulo = fig.layout.title.text
    if titulo:
        st.markdown(f"**{titulo}**")
    fig.update_layout(title=None, margin=dict(t=24))
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def _tabela(df: pd.DataFrame, **colunas) -> None:
    st.dataframe(df, width="stretch", hide_index=True, column_config=colunas)


def volume(df: pd.DataFrame) -> None:
    mensal = df.groupby(["mes", "tipo_servico"]).size().reset_index(name="chamados")
    fig = px.line(mensal, x="mes", y="chamados", color="tipo_servico", color_discrete_map=cores_atuais().por_tipo,
                  title="Chamados abertos por mês", labels=ROTULOS)
    _grafico(fig.update_xaxes(title=None, tickformat="%m/%Y"))

    esquerda, direita = st.columns(2)
    with esquerda:
        por_status = df["status"].value_counts().reset_index(name="chamados").iloc[::-1]
        _grafico(px.bar(por_status, x="chamados", y="status", orientation="h",
                        title="Chamados por status", labels=ROTULOS,
                        color_discrete_sequence=[cores_atuais().unica]).update_yaxes(title=None))
    with direita:
        por_canal = df["meio_abertura"].value_counts().reset_index(name="chamados").iloc[::-1]
        _grafico(px.bar(por_canal, x="chamados", y="meio_abertura", orientation="h",
                        title="Canal de abertura", labels=ROTULOS,
                        color_discrete_sequence=[cores_atuais().unica]).update_yaxes(title=None))


def servicos(df: pd.DataFrame) -> None:
    esquerda, direita = st.columns([1, 2])
    with esquerda:
        nivel = st.radio("Agrupar por", ["servico", "grupo_servico"], horizontal=True, format_func=ROTULOS.get)
    with direita:
        top_n = st.slider("Quantos mostrar", 5, 30, 15)

    ranking = (
        df.groupby(nivel)
        .agg(chamados=("chamado_id", "size"),
             incidentes=("tipo_servico", lambda s: int(s.eq("Incidente").sum())),
             taxa_resolucao=("resolvido", "mean"))
        .nlargest(top_n, "chamados")
        .reset_index()
    )
    fig = px.bar(ranking.iloc[::-1], x="chamados", y=nivel, orientation="h", labels=ROTULOS,
                 hover_data={"incidentes": True, "taxa_resolucao": ":.1%"},
                 color_discrete_sequence=[cores_atuais().unica], height=max(400, top_n * ALTURA_POR_BARRA),
                 title=f"Os {top_n} mais demandados")
    _grafico(fig.update_yaxes(title=None))
    st.caption(
        f"{fmt.porcentagem(parcela_servicos_genericos(df))} dos chamados caem em serviços genéricos "
        "(“99 …” ou “Outros”). Quanto maior esse número, menos o catálogo ajuda a entender a demanda."
    )


def campus(df: pd.DataFrame) -> None:
    por_campus = (
        df.groupby("campus")
        .agg(chamados=("chamado_id", "size"), taxa_resolucao=("resolvido", "mean"), backlog=("pendente", "sum"))
        .sort_values("chamados", ascending=False)
        .reset_index()
    )
    escala = list(cores_atuais().sequencial)
    fig = px.bar(por_campus, x="campus", y="chamados", color="taxa_resolucao", color_continuous_scale=escala,
                 hover_data={"backlog": True, "taxa_resolucao": ":.1%"},
                 title="Chamados por campus", labels=ROTULOS)
    fig.update_coloraxes(colorbar=dict(title="Taxa de<br>resolução", tickformat=".0%"))
    _grafico(fig.update_xaxes(title=None, tickangle=-35))

    area_campus = df.groupby(["campus", "area"]).size().reset_index(name="chamados")
    fig = px.treemap(area_campus, path=["campus", "area"], values="chamados", color="chamados",
                     color_continuous_scale=escala, title="Áreas atendidas em cada campus", labels=ROTULOS)
    _grafico(fig.update_coloraxes(showscale=False).update_traces(marker=dict(cornerradius=4)))


def satisfacao(df: pd.DataFrame) -> None:
    avaliados = df[df["nota_avaliacao"].notna()]
    if avaliados.empty:
        st.info("Nenhum chamado foi avaliado no recorte escolhido.")
        return

    esquerda, direita = st.columns(2)
    with esquerda:
        notas = avaliados["nota_avaliacao"].value_counts().sort_index().reset_index(name="chamados")
        fig = px.bar(notas, x="nota_avaliacao", y="chamados", title="Distribuição das notas",
                     labels=ROTULOS, color_discrete_sequence=[cores_atuais().unica])
        _grafico(fig.update_xaxes(dtick=1))
    with direita:
        adesao = (df[df["resolvido"]].groupby("mes")["nota_avaliacao"]
                  .apply(lambda notas_mes: notas_mes.notna().mean()).reset_index(name="adesao"))
        fig = px.line(adesao, x="mes", y="adesao", title="Chamados resolvidos que receberam nota", labels=ROTULOS)
        _grafico(fig.update_yaxes(title=None, tickformat=".0%").update_xaxes(title=None, tickformat="%m/%Y"))

    por_area = (
        avaliados.groupby("area")
        .agg(avaliacoes=("nota_avaliacao", "size"), nota_media=("nota_avaliacao", "mean"))
        .query("avaliacoes >= @MIN_AVALIACOES_POR_AREA")
        .sort_values("nota_media")
        .reset_index()
    )
    st.markdown("**Nota média por área**")
    _tabela(por_area,
            area=ROTULOS["area"],
            avaliacoes=st.column_config.NumberColumn("Avaliações", format="localized"),
            nota_media=st.column_config.NumberColumn("Nota média", format="%.2f"))
    st.caption(f"Só aparecem áreas com pelo menos {MIN_AVALIACOES_POR_AREA} avaliações.")


def automacao(df: pd.DataFrame) -> None:
    resolvidos = df[df["resolvido"]]
    if resolvidos.empty:
        st.info("Nenhum chamado resolvido no recorte escolhido.")
        return

    por_mes = resolvidos.groupby("mes")["auto"].mean().reset_index()
    fig = px.line(por_mes, x="mes", y="auto", title="Resolvidos que foram fechados automaticamente",
                  labels=ROTULOS)
    _grafico(fig.update_yaxes(title=None, tickformat=".0%").update_xaxes(title=None, tickformat="%m/%Y"))

    por_area = (
        resolvidos.groupby("area")
        .agg(resolvidos=("auto", "size"), parcela_auto=("auto", "mean"))
        .query("resolvidos >= @MIN_RESOLVIDOS_POR_AREA")
        .sort_values("parcela_auto", ascending=False)
        .reset_index()
    )
    st.markdown("**Fechamento automático por área**")
    _tabela(por_area,
            area=ROTULOS["area"],
            resolvidos=st.column_config.NumberColumn("Resolvidos", format="localized"),
            parcela_auto=st.column_config.NumberColumn("Fechados automaticamente", format="percent"))
    st.caption(
        "O fechamento automático acontece quando o usuário não confirma a solução dentro do prazo. "
        "Uma taxa alta pode indicar pouca interação, e não necessariamente eficiência."
    )


def gargalos(df: pd.DataFrame, data_referencia: pd.Timestamp) -> None:
    pendentes = pendentes_por_idade(df, data_referencia)
    if pendentes.empty:
        st.info("Não há chamados pendentes no recorte escolhido.")
    else:
        por_faixa = pendentes.groupby(["faixa", "status"], observed=True).size().reset_index(name="chamados")
        fig = px.bar(por_faixa, x="faixa", y="chamados", color="status",
                     color_discrete_map=cores_atuais().por_status_pendente,
                     title="Pendentes por tempo em aberto", labels=ROTULOS)
        _grafico(fig.update_xaxes(title=None))

        por_area = (
            pendentes.groupby("area")
            .agg(pendentes=("idade", "size"), idade_mediana=("idade", "median"))
            .sort_values("pendentes", ascending=False)
            .head(10)
            .reset_index()
        )
        st.markdown("**Áreas com mais chamados pendentes**")
        _tabela(por_area,
                area=ROTULOS["area"],
                pendentes=st.column_config.NumberColumn("Pendentes", format="localized"),
                idade_mediana=st.column_config.NumberColumn("Dias em aberto (mediana)", format="%.0f"))

    st.markdown("**Tempo até a última movimentação, por grupo de serviço**")
    manuais = df[df["resolvido"] & ~df["auto"] & df["dias_ate_ult_mov"].ge(0)]
    if manuais.empty:
        st.info("Não há chamados resolvidos manualmente no recorte escolhido.")
        return

    tempo = (
        manuais.groupby("grupo_servico")["dias_ate_ult_mov"]
        .agg(chamados="size", mediana="median", p90=lambda dias: dias.quantile(0.9))
        .query("chamados >= @MIN_CHAMADOS_POR_GRUPO")
        .sort_values("mediana", ascending=False)
        .head(15)
        .reset_index()
    )
    _tabela(tempo,
            grupo_servico=ROTULOS["grupo_servico"],
            chamados=st.column_config.NumberColumn("Chamados", format="localized"),
            mediana=st.column_config.NumberColumn("Dias (mediana)", format="%.0f"),
            p90=st.column_config.NumberColumn("Dias (9 em cada 10 até)", format="%.0f"))
    st.caption(
        "A base não tem data de fechamento, então usamos o intervalo entre a abertura e a última movimentação. "
        "Fechamentos automáticos ficam de fora porque esticam esse tempo. Trate como estimativa."
    )
