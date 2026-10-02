# BI da Central de Serviços de TI do IFMG

Painel que fiz para analisar cerca de 31 mil chamados de suporte do IFMG, de 2019 a 2026.
Dá para ver o volume ao longo do tempo, os serviços mais pedidos, como cada campus está,
as notas de satisfação, quanto é fechado automaticamente e onde os chamados ficam parados.

Feito com Python, Streamlit e Plotly. Tem modo claro e escuro.

## Rodando

```bash
pip install -r requirements.txt
streamlit run app.py
```

Abre em http://localhost:8501. A base já vem em `dados/`, mas dá para enviar outro CSV pela barra lateral.

## Alguns cuidados com os números

- A taxa de resolução não conta os chamados cancelados.
- A base não tem data de fechamento, então o tempo de atendimento é estimado pela última movimentação do chamado.
- Só um terço dos chamados resolvidos recebe nota, então a nota média (4,94) deve ser lida com cautela.

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```
