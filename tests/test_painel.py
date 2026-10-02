import pandas as pd
import pytest

from painel import formatacao as fmt
from painel.dados import BaseInvalidaError, preparar
from painel.filtros import Filtros, aplicar_filtros
from painel.indicadores import calcular_indicadores, parcela_servicos_genericos, pendentes_por_idade


def _linha(chamado_id, status, abertura="2024-01-10", ultima="2024-01-15", auto="", nota=None,
           area="TI", campus="REITORIA", tipo="Requisição", servico="Senha"):
    return {
        "chamado_id": chamado_id, "data_abertura": abertura, "data_ultima_movimentacao": ultima,
        "area": area, "grupo_servico": "Contas", "servico": servico, "tipo_servico": tipo,
        "campus": campus, "status": status, "meio_abertura": "web",
        "fechado_automaticamente": auto, "nota_avaliacao": nota,
    }


@pytest.fixture
def base():
    return preparar(pd.DataFrame([
        _linha(1, "Fechado", nota=5),
        _linha(2, "Fechado", auto="Y"),
        _linha(3, "Resolvido", nota=3, servico="99 Outros serviços"),
        _linha(4, "Aberto", abertura="2023-05-01", campus="OURO PRETO", tipo="Incidente"),
        _linha(5, "Cancelado", area="Administrativo"),
    ]))


def test_preparar_recusa_base_sem_colunas_obrigatorias():
    with pytest.raises(BaseInvalidaError, match="status"):
        preparar(pd.DataFrame([_linha(1, "Fechado")]).drop(columns="status"))


def test_preparar_descarta_data_de_abertura_invalida():
    df = preparar(pd.DataFrame([_linha(1, "Fechado"), _linha(2, "Fechado", abertura="não é data")]))
    assert df["chamado_id"].tolist() == [1]


def test_preparar_marca_resolvido_pendente_e_fechamento_automatico(base):
    assert base["resolvido"].tolist() == [True, True, True, False, False]
    assert base["pendente"].tolist() == [False, False, False, True, False]
    assert base["auto"].tolist() == [False, True, False, False, False]
    assert base["dias_ate_ult_mov"].iloc[0] == 5


def test_indicadores_tiram_cancelados_da_taxa_de_resolucao(base):
    ind = calcular_indicadores(base)
    assert ind.total == 5
    assert ind.backlog == 1
    assert ind.taxa_resolucao == pytest.approx(3 / 4)
    assert ind.taxa_resolucao_bruta == pytest.approx(3 / 5)
    assert ind.taxa_fechamento_auto == pytest.approx(1 / 3)
    assert ind.nota_media == pytest.approx(4.0)
    assert ind.adesao_avaliacao == pytest.approx(2 / 3)


def test_indicadores_sem_resolvidos_nao_dividem_por_zero(base):
    ind = calcular_indicadores(base[base["status"].eq("Aberto")])
    assert ind.taxa_fechamento_auto is None
    assert ind.nota_media is None


def test_parcela_de_servicos_genericos(base):
    assert parcela_servicos_genericos(base) == pytest.approx(1 / 5)


def test_pendentes_recebem_idade_e_faixa(base):
    pendentes = pendentes_por_idade(base, pd.Timestamp("2024-01-10"))
    assert pendentes["idade"].tolist() == [254]
    assert pendentes["faixa"].astype(str).tolist() == ["91 dias a 1 ano"]


def test_filtros_vazios_significam_todos(base):
    assert len(aplicar_filtros(base, Filtros(2023, 2024))) == 5
    assert aplicar_filtros(base, Filtros(2024, 2024))["chamado_id"].tolist() == [1, 2, 3, 5]
    assert aplicar_filtros(base, Filtros(2023, 2024, campi=("OURO PRETO",)))["chamado_id"].tolist() == [4]


@pytest.mark.parametrize("valor, esperado", [(0.9391, "93,9%"), (None, "—"), (float("nan"), "—")])
def test_porcentagem(valor, esperado):
    assert fmt.porcentagem(valor) == esperado


def test_numero_usa_separadores_brasileiros():
    assert fmt.numero(31541) == "31.541"
    assert fmt.numero(4.9353, 2) == "4,94"


def test_mes_ano():
    assert fmt.mes_ano(pd.Timestamp("2019-06-10")) == "jun/2019"
