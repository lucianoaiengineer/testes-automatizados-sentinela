"""Comparação pareada por motor, com preservação das séries dentro do grupo."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray

METRICAS = ("acuracia", "precisao", "recall", "f1")
SEMENTE = 42
REPETICOES = 2000


def metricas_contagens(contagens: NDArray[np.float64]) -> NDArray[np.float64]:
    """Calcula métricas para matrizes [..., vp/vn/fp/fn], com zero por convenção.

    A convenção para denominadores nulos acompanha o painel do Sentinela.
    Contagens negativas, não finitas e formatos inválidos são rejeitados.
    """
    valores = np.asarray(contagens, dtype=float)
    if valores.ndim < 1 or valores.shape[-1] != 4:
        raise ValueError("Esperadas quatro contagens: vp, vn, fp, fn")
    if not np.isfinite(valores).all() or (valores < 0).any():
        raise ValueError("Contagens precisam ser finitas e não negativas")
    vp, vn, fp, fn = np.moveaxis(valores, -1, 0)

    def dividir(numerador: NDArray, denominador: NDArray) -> NDArray:
        return np.divide(
            numerador,
            denominador,
            out=np.zeros_like(numerador, dtype=float),
            where=denominador != 0,
        )

    return np.stack(
        [
            dividir(vp + vn, vp + vn + fp + fn),
            dividir(vp, vp + fp),
            dividir(vp, vp + fn),
            dividir(2 * vp, 2 * vp + fp + fn),
        ],
        axis=-1,
    )


def comparar_pareado(
    previsoes: pd.DataFrame,
    repeticoes: int = REPETICOES,
    semente: int = SEMENTE,
) -> pd.DataFrame:
    """Estima IC percentil de 95% para v2 menos v1, reamostrando motores.

    Cada sorteio inclui toda a série do motor nas duas versões. Pressupõe
    grupos aproximadamente independentes; choques comuns da planta limitam
    essa interpretação. Não reestima modelos ou features durante o bootstrap.
    """
    obrigatorias = {"id_maquina", "falha_72h", "predicao_v1", "predicao_v2"}
    if not obrigatorias <= set(previsoes) or previsoes.empty or repeticoes < 2:
        raise ValueError("Dados ausentes ou número de reamostragens inválido")
    if previsoes[list(obrigatorias)].isna().any().any():
        raise ValueError("A comparação não admite valores ausentes")
    for coluna in ("falha_72h", "predicao_v1", "predicao_v2"):
        if not previsoes[coluna].isin([0, 1]).all():
            raise ValueError("Alvo e decisões devem ser binários")
    grupos = []
    for _, grupo in previsoes.groupby("id_maquina", sort=True):
        real = grupo["falha_72h"].to_numpy()
        versoes = []
        for versao in ("v1", "v2"):
            predito = grupo[f"predicao_{versao}"].to_numpy()
            versoes.append(
                [
                    np.sum((real == 1) & (predito == 1)),
                    np.sum((real == 0) & (predito == 0)),
                    np.sum((real == 0) & (predito == 1)),
                    np.sum((real == 1) & (predito == 0)),
                ]
            )
        grupos.append(versoes)
    contagens = np.asarray(grupos, dtype=float)
    if len(grupos) < 2:
        raise ValueError("São necessários pelo menos dois motores")
    gerador = np.random.default_rng(semente)
    indices = gerador.integers(0, len(grupos), (repeticoes, len(grupos)))
    metricas = metricas_contagens(contagens[indices].sum(axis=1))
    diferencas = metricas[:, 1] - metricas[:, 0]
    pontuais = metricas_contagens(contagens.sum(axis=0))
    limites = np.quantile(diferencas, [0.025, 0.975], axis=0)
    return pd.DataFrame(
        {
            "metrica": METRICAS,
            "v1": pontuais[0],
            "v2": pontuais[1],
            "diferenca_v2_v1": pontuais[1] - pontuais[0],
            "ic_inferior": limites[0],
            "ic_superior": limites[1],
            "motores": len(grupos),
            "repeticoes": repeticoes,
            "semente": semente,
        }
    )
