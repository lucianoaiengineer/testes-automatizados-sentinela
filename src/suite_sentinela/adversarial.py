"""Intervenções controladas e medições sem impor tolerâncias não documentadas."""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray


def medir_mudanca(originais: NDArray, alteradas: NDArray) -> dict[str, float | int]:
    """Conta mudanças de decisão a 0,5 e deslocamentos de probabilidades."""
    primeiro = np.asarray(originais, dtype=float)
    segundo = np.asarray(alteradas, dtype=float)
    if primeiro.ndim != 1 or segundo.shape != primeiro.shape or not primeiro.size:
        raise ValueError("Probabilidades precisam ser vetores alinhados e não vazios")
    if not all(
        np.isfinite(v).all() and ((v >= 0) & (v <= 1)).all()
        for v in (primeiro, segundo)
    ):
        raise ValueError("Probabilidades devem ser finitas e pertencer a [0, 1]")
    mascara = (primeiro >= 0.5) != (segundo >= 0.5)
    return {
        "linhas": len(primeiro),
        "mudancas": int(mascara.sum()),
        "taxa_mudanca": float(mascara.mean()),
        "ordens_abertas": int(np.sum((primeiro < 0.5) & (segundo >= 0.5))),
        "ordens_canceladas": int(np.sum((primeiro >= 0.5) & (segundo < 0.5))),
        "delta_proba_medio": float(np.abs(segundo - primeiro).mean()),
        "delta_proba_maximo": float(np.abs(segundo - primeiro).max()),
    }


def perturbar_temperatura(quadro: pd.DataFrame, deslocamento: float) -> pd.DataFrame:
    """Desloca somente temperatura dentro da faixa, usando menos de 1 °C.

    O recorte nos limites preserva a faixa, mas pode reduzir a perturbação
    efetiva. As análises registram a magnitude efetiva e linhas afetadas.
    """
    if not np.isfinite(deslocamento) or not 0 < abs(deslocamento) < 1:
        raise ValueError("Deslocamento deve ser não nulo e inferior a 1 °C")
    if not quadro["temperatura_c"].between(45, 95).all():
        raise ValueError("Perturbação requer temperaturas inicialmente válidas")
    alterado = quadro.copy(deep=True)
    alterado["temperatura_c"] = (alterado["temperatura_c"] + deslocamento).clip(45, 95)
    return alterado


def permutar_feature(
    quadro: pd.DataFrame, coluna: str, semente: int = 42
) -> pd.DataFrame:
    """Permuta uma coluna mantendo sua distribuição marginal e as demais fixas.

    A intervenção quebra correlações e mede dependência funcional, não efeito
    causal ou validade física das combinações resultantes.
    """
    if coluna not in quadro:
        raise ValueError("Feature ausente")
    alterado = quadro.copy(deep=True)
    alterado[coluna] = np.random.default_rng(semente).permutation(
        quadro[coluna].to_numpy()
    )
    return alterado
