"""Faixas de confiabilidade e varredura descritiva do limiar de decisão."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from suite_sentinela.estatistica import metricas_contagens


def validar_probabilidades(
    reais: NDArray,
    probabilidades: NDArray,
) -> tuple[NDArray, NDArray]:
    """Valida vetores binários e probabilidades alinhadas; rejeita lote vazio."""
    alvo = np.asarray(reais)
    valores = np.asarray(probabilidades, dtype=float)
    if alvo.ndim != 1 or valores.shape != alvo.shape or not len(alvo):
        raise ValueError(
            "Alvos e probabilidades devem ser vetores não vazios alinhados"
        )
    if not np.isin(alvo, [0, 1]).all():
        raise ValueError("Alvo precisa ser binário")
    if not np.isfinite(valores).all() or ((valores < 0) | (valores > 1)).any():
        raise ValueError("Probabilidades devem ser finitas e pertencer a [0, 1]")
    return alvo, valores


def avaliar_calibracao(
    reais: NDArray,
    probabilidades: NDArray,
    faixas: int = 10,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Agrupa [0,1] em faixas iguais, incluindo 1 na última, e mede Brier/ECE.

    Faixas vazias permanecem explícitas, sem frequência estimada. ECE depende
    da escolha das faixas e não tem aqui um limite contratual de aprovação.
    """
    alvo, valores = validar_probabilidades(reais, probabilidades)
    if faixas < 1:
        raise ValueError("O número de faixas precisa ser positivo")
    indices = np.minimum((valores * faixas).astype(int), faixas - 1)
    linhas = []
    erro_calibracao = 0.0
    for faixa in range(faixas):
        mascara = indices == faixa
        quantidade = int(mascara.sum())
        media = float(valores[mascara].mean()) if quantidade else None
        frequencia = float(alvo[mascara].mean()) if quantidade else None
        if media is not None and frequencia is not None:
            erro_calibracao += quantidade / len(alvo) * abs(media - frequencia)
        linhas.append(
            {
                "inicio": faixa / faixas,
                "fim": (faixa + 1) / faixas,
                "quantidade": quantidade,
                "probabilidade_media": media,
                "frequencia_observada": frequencia,
            }
        )
    return pd.DataFrame(linhas), {
        "brier": float(np.mean((valores - alvo) ** 2)),
        "ece": erro_calibracao,
    }


def varrer_limiar(reais: NDArray, probabilidades: NDArray) -> pd.DataFrame:
    """Mede 101 limiares fixos; a varredura não seleciona limiar para produção."""
    alvo, valores = validar_probabilidades(reais, probabilidades)
    linhas = []
    for limiar in np.linspace(0, 1, 101):
        decisoes = valores >= limiar
        vp = np.sum((alvo == 1) & decisoes)
        vn = np.sum((alvo == 0) & ~decisoes)
        fp = np.sum((alvo == 0) & decisoes)
        fn = np.sum((alvo == 1) & ~decisoes)
        metricas = metricas_contagens(np.array([vp, vn, fp, fn], dtype=float))
        linhas.append(
            {
                "limiar": limiar,
                "vp": vp,
                "vn": vn,
                "fp": fp,
                "fn": fn,
                "acuracia": metricas[0],
                "precisao": metricas[1],
                "recall": metricas[2],
                "f1": metricas[3],
            }
        )
    return pd.DataFrame(linhas)
