"""Mede as duas versões nos três conjuntos, com e sem o alvo na entrada."""

from pathlib import Path

import pandas as pd
import sentinela as sn


def executar_linha_base() -> None:
    """Grava métricas e previsões; não modifica dados ou artefatos originais."""
    destino = Path(__file__).resolve().parents[1] / "resultados"
    destino.mkdir(exist_ok=True)
    resumos = []
    for conjunto in sn.dados.CONJUNTOS:
        bruto = sn.dados.carregar(conjunto)
        limpo = sn.preprocessamento.limpar(bruto)
        reais = limpo["falha_72h"].to_numpy()
        for modo in ("rotulado", "sem_alvo"):
            entrada = bruto if modo == "rotulado" else bruto.drop(columns="falha_72h")
            previsoes = limpo[["id_maquina", "timestamp", "falha_72h"]].copy()
            for versao in sn.modelo.VERSOES:
                saida = sn.pipeline.executar(entrada, versao=versao)
                resumos.append(
                    {
                        "conjunto": conjunto,
                        "modo": modo,
                        "versao": versao,
                        "linhas_brutas": len(bruto),
                        "linhas_validas": len(saida),
                        "prevalencia": float(reais.mean()),
                        "acuracia_trivial": float((reais == 0).mean()),
                        **sn.avaliacao.matriz_confusao(reais, saida["predicao"]),
                        **sn.avaliacao.metricas(reais, saida["predicao"]),
                    }
                )
                previsoes[f"probabilidade_{versao}"] = saida["probabilidade"]
                previsoes[f"predicao_{versao}"] = saida["predicao"]
            previsoes.to_csv(destino / f"previsoes_{conjunto}_{modo}.csv", index=False)
    pd.DataFrame(resumos).to_csv(destino / "linha_base.csv", index=False)
    print("Linha de base: resultados/linha_base.csv; 12 avaliações")


if __name__ == "__main__":
    executar_linha_base()
