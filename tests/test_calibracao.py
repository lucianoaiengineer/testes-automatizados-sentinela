"""Oráculos de calibração e relações válidas ao variar o limiar."""

import numpy as np
import pytest

from suite_sentinela.calibracao import (
    avaliar_calibracao,
    validar_probabilidades,
    varrer_limiar,
)

pytestmark = pytest.mark.rapido


def test_calibracao_perfeita_inclui_probabilidade_um_e_faixas_vazias() -> None:
    """Probabilidades exatas devem ter Brier e ECE zero, sem perder p=1."""
    faixas, resumo = avaliar_calibracao(np.array([0, 1]), np.array([0.0, 1.0]))
    assert resumo == {"brier": 0, "ece": 0}
    assert faixas["quantidade"].sum() == 2
    assert faixas.iloc[-1]["quantidade"] == 1
    assert faixas["frequencia_observada"].isna().sum() == 8


def test_probabilidade_constante_reproduz_frequencia_observada() -> None:
    """Previsão 0,5 com metade positiva tem ECE zero e Brier 0,25."""
    _, resumo = avaliar_calibracao(np.array([0, 1]), np.array([0.5, 0.5]))
    assert resumo == pytest.approx({"brier": 0.25, "ece": 0})


def test_varredura_tem_limiar_padrao_e_recall_nao_crescente() -> None:
    """A precisão não é imposta como monotônica; positivos e recall são."""
    tabela = varrer_limiar(np.array([0, 1, 1, 0]), np.array([0.1, 0.4, 0.5, 0.9]))
    assert len(tabela) == 101
    assert tabela["recall"].diff().dropna().le(0).all()
    assert (tabela["vp"] + tabela["fp"]).diff().dropna().le(0).all()
    padrao = tabela.loc[np.isclose(tabela["limiar"], 0.5)].iloc[0]
    assert padrao["vp"] == padrao["fp"] == padrao["fn"] == padrao["vn"] == 1


@pytest.mark.parametrize(
    "alvo,probabilidades",
    [([], []), ([1], []), ([2], [0.5]), ([1], [np.nan]), ([1], [1.1])],
)
def test_calibracao_rejeita_vetores_invalidos(alvo: list, probabilidades: list) -> None:
    """Entradas sem significado probabilístico não geram métricas."""
    with pytest.raises(ValueError):
        validar_probabilidades(np.array(alvo), np.array(probabilidades))


def test_numero_de_faixas_deve_ser_positivo() -> None:
    """Evita uma partição vazia do intervalo probabilístico."""
    with pytest.raises(ValueError):
        avaliar_calibracao(np.array([1]), np.array([1.0]), faixas=0)
