"""Mudança de distribuição: localização, dispersão, caudas e comparação por motor."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy import stats


def ajustar_holm(valores: NDArray) -> NDArray:
    """Controla multiplicidade pelo procedimento de Holm, preservando a ordem."""
    probabilidades = np.asarray(valores, dtype=float)
    if probabilidades.ndim != 1 or not np.isfinite(probabilidades).all():
        raise ValueError("Esperado vetor finito de p-valores")
    if ((probabilidades < 0) | (probabilidades > 1)).any():
        raise ValueError("P-valores devem pertencer a [0, 1]")
    ordem = np.argsort(probabilidades)
    ajustados = np.empty_like(probabilidades)
    ajustados[ordem] = np.minimum(
        1,
        np.maximum.accumulate(probabilidades[ordem] * np.arange(len(ordem), 0, -1)),
    )
    return ajustados


def comparar_distribuicao(
    teste: pd.DataFrame,
    producao: pd.DataFrame,
    coluna: str,
    repeticoes: int = 1999,
    semente: int = 42,
) -> dict[str, float | int | str]:
    """Compara a coluna e permuta pares de períodos inteiros por motor.

    O KS nominal assume observações independentes e é apenas referência.
    A permutação troca teste/produção dentro de cada motor em uma grade de
    201 quantis comuns, dando peso igual a cada motor. Depende da hipótese de
    permutabilidade dos períodos; não demonstra ausência de drift conceitual.
    """
    if repeticoes < 1:
        raise ValueError("Número de permutações precisa ser positivo")
    valores_teste = teste[coluna].dropna().to_numpy(dtype=float)
    valores_producao = producao[coluna].dropna().to_numpy(dtype=float)
    if min(len(valores_teste), len(valores_producao)) < 2:
        raise ValueError("Comparação exige duas observações válidas em cada período")
    if not all(
        np.isfinite(valores).all() for valores in (valores_teste, valores_producao)
    ):
        raise ValueError("Valores não finitos não são aceitos")
    motores = sorted(set(teste["id_maquina"]) & set(producao["id_maquina"]))
    if set(teste["id_maquina"]) != set(producao["id_maquina"]) or len(motores) < 2:
        raise ValueError("Os períodos devem conter os mesmos motores, no mínimo dois")
    grade = np.unique(
        np.quantile(
            np.concatenate([valores_teste, valores_producao]),
            np.linspace(0, 1, 201),
        )
    )
    diferencas = []
    for motor in motores:
        curvas = []
        for quadro in (teste, producao):
            amostra = np.sort(
                quadro.loc[quadro["id_maquina"] == motor, coluna].dropna()
            )
            if not len(amostra):
                raise ValueError("Motor sem observações válidas em um período")
            curvas.append(np.searchsorted(amostra, grade, side="right") / len(amostra))
        diferencas.append(curvas[1] - curvas[0])
    matriz = np.asarray(diferencas)
    observado = float(np.max(np.abs(matriz.mean(axis=0))))
    sinais = np.random.default_rng(semente).choice([-1, 1], (repeticoes, len(motores)))
    simulados = np.max(np.abs(sinais @ matriz / len(motores)), axis=1)
    p_blocos = float((1 + np.sum(simulados >= observado - 1e-12)) / (1 + repeticoes))
    ks = stats.ks_2samp(valores_teste, valores_producao)
    variancia_teste = float(np.var(valores_teste, ddof=1))
    variancia_producao = float(np.var(valores_producao, ddof=1))
    escala = np.sqrt((variancia_teste + variancia_producao) / 2)
    diferenca_media = float(valores_producao.mean() - valores_teste.mean())
    caudas = np.quantile(valores_teste, [0.01, 0.99])
    resumo: dict[str, float | int | str] = {
        "coluna": coluna,
        "n_teste": len(valores_teste),
        "n_producao": len(valores_producao),
        "media_teste": float(valores_teste.mean()),
        "media_producao": float(valores_producao.mean()),
        "variancia_teste": variancia_teste,
        "variancia_producao": variancia_producao,
        "diferenca_media": diferenca_media,
        "diferenca_padronizada": (
            float(diferenca_media / escala)
            if escala
            else (0.0 if diferenca_media == 0 else float("nan"))
        ),
        "ks": float(ks.statistic),
        "p_ks_iid_exploratorio": float(ks.pvalue),
        "wasserstein": float(
            stats.wasserstein_distance(valores_teste, valores_producao)
        ),
        "d_grade_por_motor": observado,
        "p_permutacao_motor": p_blocos,
        "cauda_producao_fora_p01_p99_teste": float(
            np.mean(
                (valores_producao < caudas[0]) | (valores_producao > caudas[1]),
            )
        ),
        "motores": len(motores),
        "permutacoes": repeticoes,
    }
    for nome, valores in (("teste", valores_teste), ("producao", valores_producao)):
        for quantil in (1, 5, 50, 95, 99):
            resumo[f"p{quantil:02d}_{nome}"] = float(np.percentile(valores, quantil))
    return resumo
