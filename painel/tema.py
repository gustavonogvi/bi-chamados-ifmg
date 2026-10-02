"""Identidade visual dos gráficos, nos modos claro e escuro.

As paletas foram validadas para daltonismo contra o fundo de cada modo; a ordem dos slots
faz parte da validação, então não reordene. Cada entidade tem cor fixa, para não mudar
quando um filtro tira séries.

Cor de texto, grade e eixos fica a cargo do tema do Streamlit, que acompanha o modo
no navegador. Aqui só definimos a cor dos dados.
"""
from __future__ import annotations

from dataclasses import dataclass

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

FONTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

_CATEGORICA_CLARO = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948")
_CATEGORICA_ESCURO = ("#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767")
# Do quase zero ao máximo: no claro o valor baixo some no fundo branco, no escuro some no fundo escuro.
_SEQUENCIAL_CLARO = ("#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b")
_SEQUENCIAL_ESCURO = ("#184f95", "#1c5cab", "#256abf", "#3987e5", "#6da7ec", "#b7d3f6")


@dataclass(frozen=True)
class Cores:
    categorica: tuple[str, ...]
    sequencial: tuple[str, ...]

    @property
    def unica(self) -> str:
        return self.categorica[0]

    @property
    def por_tipo(self) -> dict[str, str]:
        return {"Requisição": self.categorica[0], "Incidente": self.categorica[1]}

    @property
    def por_status_pendente(self) -> dict[str, str]:
        status = ("Aberto", "Em atendimento", "Suspenso", "Reaberto")
        return dict(zip(status, self.categorica))


CLARO = Cores(_CATEGORICA_CLARO, _SEQUENCIAL_CLARO)
ESCURO = Cores(_CATEGORICA_ESCURO, _SEQUENCIAL_ESCURO)

# Nomes de coluna como aparecem para quem lê o painel.
ROTULOS = {
    "mes": "Mês",
    "chamados": "Chamados",
    "tipo_servico": "Tipo",
    "status": "Status",
    "meio_abertura": "Canal",
    "servico": "Serviço",
    "grupo_servico": "Grupo de serviço",
    "area": "Área",
    "campus": "Campus",
    "incidentes": "Incidentes",
    "taxa_resolucao": "Taxa de resolução",
    "backlog": "Pendentes",
    "nota_avaliacao": "Nota",
    "adesao": "Adesão",
    "auto": "Fechamento automático",
    "faixa": "Tempo em aberto",
}


def cores_atuais() -> Cores:
    """Paleta do modo que o navegador está mostrando (claro, se não der para saber)."""
    modo = getattr(st.context.theme, "type", None)
    return ESCURO if modo == "dark" else CLARO


def _template() -> go.layout.Template:
    return go.layout.Template(
        layout=dict(
            font=dict(family=FONTE, size=13),
            title=dict(font=dict(size=15), x=0, xanchor="left"),
            separators=",.",
            margin=dict(l=8, r=8, t=48, b=8),
            hoverlabel=dict(font_family=FONTE),
            barcornerradius=4,
            bargap=0.25,
        ),
        data=dict(scatter=[go.Scatter(line=dict(width=2))]),
    )


def aplicar_tema() -> None:
    pio.templates["ifmg"] = _template()
    pio.templates.default = "ifmg"
