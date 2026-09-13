"""Mede ruído térmico, permutações e contrafactuais sobre teste e produção."""

from pathlib import Path

import numpy as np
import pandas as pd
import sentinela as sn

from suite_sentinela.adversarial import (
    medir_mudanca,
    permutar_feature,
    perturbar_temperatura,
)


def executar_analise_adversarial() -> None:
    """Usa o alvo somente para análise posterior, sem fornecê-lo ao modelo."""
    destino = Path(__file__).resolve().parents[1] / "resultados"
    medicoes, detalhes, associacoes = [], [], []
    for conjunto in ("teste", "producao"):
        bruto = sn.dados.carregar(conjunto)
        entrada = bruto.drop(columns="falha_72h")
        limpo = sn.preprocessamento.limpar(entrada)
        features = sn.features.construir(limpo)
        for versao in sn.modelo.VERSOES:
            modelo = sn.modelo.carregar(versao)
            originais = modelo.prever_proba(features)
            for deslocamento in (-0.4, 0.4):
                alterado = perturbar_temperatura(entrada, deslocamento)
                resultado = sn.pipeline.executar(alterado, versao=versao)
                alteradas = resultado["probabilidade"].to_numpy()
                delta = alterado["temperatura_c"] - entrada["temperatura_c"]
                nome = f"temperatura_{deslocamento:+.1f}"
                medicoes.append(
                    {
                        "conjunto": conjunto,
                        "versao": versao,
                        "intervencao": nome,
                        "campo": "temperatura_c",
                        "tipo": "ruido_sensor",
                        "magnitude_maxima": float(delta.abs().max()),
                        **medir_mudanca(originais, alteradas),
                    }
                )
                for indice in np.flatnonzero((originais >= 0.5) != (alteradas >= 0.5)):
                    detalhes.append(
                        {
                            "conjunto": conjunto,
                            "versao": versao,
                            "intervencao": nome,
                            "id_maquina": limpo.loc[indice, "id_maquina"],
                            "timestamp": limpo.loc[indice, "timestamp"],
                            "probabilidade_original": originais[indice],
                            "probabilidade_alterada": alteradas[indice],
                        }
                    )
            for coluna in sn.features.ORDEM_FEATURES:
                alteradas = modelo.prever_proba(permutar_feature(features, coluna))
                medicoes.append(
                    {
                        "conjunto": conjunto,
                        "versao": versao,
                        "intervencao": "permutacao",
                        "campo": coluna,
                        "tipo": "feature_isolada",
                        **medir_mudanca(originais, alteradas),
                    }
                )
            for coluna, primeiro, segundo in (
                ("id_operador", "OP-01", "OP-07"),
                ("turno", 1, 3),
            ):
                primeira = sn.pipeline.executar(
                    entrada.assign(**{coluna: primeiro}), versao=versao
                )
                segunda = sn.pipeline.executar(
                    entrada.assign(**{coluna: segundo}), versao=versao
                )
                medicoes.append(
                    {
                        "conjunto": conjunto,
                        "versao": versao,
                        "intervencao": f"{primeiro}_para_{segundo}",
                        "campo": coluna,
                        "tipo": "contrafactual",
                        **medir_mudanca(
                            primeira["probabilidade"].to_numpy(),
                            segunda["probabilidade"].to_numpy(),
                        ),
                    }
                )
        normalizado = sn.preprocessamento.limpar(bruto)
        for operador, grupo in normalizado.groupby("id_operador"):
            associacoes.append(
                {
                    "conjunto": conjunto,
                    "operador": operador,
                    "linhas": len(grupo),
                    "falhas": int(grupo["falha_72h"].sum()),
                    "prevalencia": float(grupo["falha_72h"].mean()),
                }
            )
    pd.DataFrame(medicoes).to_csv(destino / "adversarial.csv", index=False)
    pd.DataFrame(detalhes).to_csv(destino / "mudancas_ruido.csv", index=False)
    pd.DataFrame(associacoes).to_csv(destino / "associacao_operador.csv", index=False)
    print("Análises adversariais: resultados/adversarial.csv e registros de mudanças")


if __name__ == "__main__":
    executar_analise_adversarial()
