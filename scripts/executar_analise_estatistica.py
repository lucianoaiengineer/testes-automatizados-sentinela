"""Produz comparações pareadas, limiares, calibração e diagnóstico de distribuição."""

from pathlib import Path

import pandas as pd
import sentinela as sn

from suite_sentinela.calibracao import avaliar_calibracao, varrer_limiar
from suite_sentinela.contratos import FAIXAS, pressao_em_bar
from suite_sentinela.distribuicoes import ajustar_holm, comparar_distribuicao
from suite_sentinela.estatistica import comparar_pareado


def executar_analise_estatistica() -> None:
    """Consome a linha de base salva e grava tabelas sem escolher limiar operacional."""
    destino = Path(__file__).resolve().parents[1] / "resultados"
    comparacoes, calibracoes, resumos, limiares = [], [], [], []
    for conjunto in sn.dados.CONJUNTOS:
        for modo in ("rotulado", "sem_alvo"):
            previsoes = pd.read_csv(destino / f"previsoes_{conjunto}_{modo}.csv")
            comparacoes.append(
                comparar_pareado(previsoes).assign(conjunto=conjunto, modo=modo)
            )
            for versao in sn.modelo.VERSOES:
                alvo = previsoes["falha_72h"].to_numpy()
                probabilidades = previsoes[f"probabilidade_{versao}"].to_numpy()
                tabela, resumo = avaliar_calibracao(alvo, probabilidades)
                identificacao = {"conjunto": conjunto, "modo": modo, "versao": versao}
                calibracoes.append(tabela.assign(**identificacao))
                resumos.append({**identificacao, **resumo})
                limiares.append(
                    varrer_limiar(alvo, probabilidades).assign(**identificacao)
                )
    for nome, quadros in (
        ("comparacao_pareada", comparacoes),
        ("calibracao_faixas", calibracoes),
        ("varredura_limiar", limiares),
    ):
        pd.concat(quadros, ignore_index=True).to_csv(
            destino / f"{nome}.csv", index=False
        )
    pd.DataFrame(resumos).to_csv(destino / "calibracao_resumo.csv", index=False)
    periodos = []
    for conjunto in ("teste", "producao"):
        bruto = sn.dados.carregar(conjunto)
        # A comparação física de pressão usa bar nos dois períodos. O pipeline
        # avaliado permanece intacto; esta conversão pertence só à auditoria.
        bruto["pressao"] = pressao_em_bar(bruto)
        bruto["id_maquina"] = bruto["id_maquina"].str.strip().str.upper()
        periodos.append(bruto)
    distribuicoes = pd.DataFrame(
        [
            comparar_distribuicao(periodos[0], periodos[1], coluna)
            for coluna in [*FAIXAS, "horas_operacao", "turno"]
        ]
    )
    distribuicoes["p_holm"] = ajustar_holm(
        distribuicoes["p_permutacao_motor"].to_numpy()
    )
    distribuicoes.to_csv(destino / "distribuicoes.csv", index=False)
    categorias = []
    for conjunto in sn.dados.CONJUNTOS:
        bruto = sn.dados.carregar(conjunto)
        for coluna in ("id_operador", "id_maquina", "unidade_pressao", "falha_72h"):
            valores = bruto[coluna].astype(str).str.strip().str.upper()
            for categoria, quantidade in valores.value_counts().items():
                categorias.append(
                    {
                        "conjunto": conjunto,
                        "coluna": coluna,
                        "categoria": categoria,
                        "quantidade": quantidade,
                        "proporcao": quantidade / len(bruto),
                    }
                )
    pd.DataFrame(categorias).to_csv(
        destino / "distribuicoes_categoricas.csv", index=False
    )
    print("Análises estatísticas: tabelas gravadas em resultados/")


if __name__ == "__main__":
    executar_analise_estatistica()
