"""Validação dos cálculos auxiliares e comparação real, pareada por motor."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn

from suite_sentinela.contratos import RAIZ
from suite_sentinela.estatistica import comparar_pareado, metricas_contagens


@pytest.mark.rapido
def test_matriz_e_metricas_possuem_oraculo_conhecido() -> None:
    """Contagens escolhidas à mão validam denominadores e a classe positiva."""
    real, predito = [1, 1, 1, 0, 0, 0], [1, 1, 0, 1, 0, 0]
    assert sn.avaliacao.matriz_confusao(real, predito) == {
        "vp": 2,
        "vn": 2,
        "fp": 1,
        "fn": 1,
    }
    assert sn.avaliacao.metricas(real, predito) == pytest.approx(
        {"acuracia": 2 / 3, "precisao": 2 / 3, "recall": 2 / 3, "f1": 2 / 3}
    )
    np.testing.assert_allclose(
        metricas_contagens(np.array([2.0, 2.0, 1.0, 1.0])), 2 / 3
    )


@pytest.mark.rapido
def test_metricas_tratam_denominadores_nulos_e_formas_distintas() -> None:
    """A convenção de zero não pode produzir NaN no painel ou no bootstrap."""
    assert sn.avaliacao.metricas([0, 0], [0, 0]) == {
        "acuracia": 1,
        "precisao": 0,
        "recall": 0,
        "f1": 0,
    }
    np.testing.assert_array_equal(metricas_contagens(np.zeros(4)), np.zeros(4))
    with pytest.raises(ValueError, match="tamanhos diferentes"):
        sn.avaliacao.metricas([0], [0, 1])


@pytest.mark.rapido
@pytest.mark.parametrize("contagens", [[-1, 0, 0, 0], [np.nan, 0, 0, 0], [1, 2]])
def test_contagens_invalidas_sao_rejeitadas(contagens: list[float]) -> None:
    """O cálculo externo não aceita contagens sem interpretação estatística."""
    with pytest.raises(ValueError):
        metricas_contagens(np.asarray(contagens))


@pytest.mark.rapido
def test_bootstrap_pareado_detecta_sinal_e_preserva_identidade() -> None:
    """Uma versão perfeita e outra sempre errada fornecem diferenças exatas."""
    quadro = pd.DataFrame(
        {
            "id_maquina": ["A", "A", "B", "B"],
            "falha_72h": [0, 1, 0, 1],
            "predicao_v1": [1, 0, 1, 0],
            "predicao_v2": [0, 1, 0, 1],
        }
    )
    comparacao = comparar_pareado(quadro, repeticoes=100)
    assert comparacao["ic_inferior"].eq(1).all()
    pd.testing.assert_frame_equal(comparacao, comparar_pareado(quadro, repeticoes=100))
    quadro["predicao_v1"] = quadro["predicao_v2"]
    identidade = comparar_pareado(quadro, repeticoes=100)
    assert identidade["ic_inferior"].eq(0).all()
    assert identidade["ic_superior"].eq(0).all()


@pytest.mark.rapido
@pytest.mark.parametrize(
    "caso", ["vazio", "grupo_unico", "nao_binario", "ausente", "repeticoes"]
)
def test_bootstrap_rejeita_amostra_invalida(caso: str) -> None:
    """A validação evita intervalos calculados sobre amostras malformadas."""
    quadro = pd.DataFrame(
        {
            "id_maquina": ["A", "B"],
            "falha_72h": [0, 1],
            "predicao_v1": [0, 1],
            "predicao_v2": [0, 1],
        }
    )
    if caso == "vazio":
        quadro = quadro.iloc[:0]
    elif caso == "grupo_unico":
        quadro["id_maquina"] = "A"
    elif caso == "nao_binario":
        quadro["predicao_v2"] = 2
    elif caso == "ausente":
        quadro["id_maquina"] = None
    with pytest.raises(ValueError):
        comparar_pareado(quadro, repeticoes=1 if caso == "repeticoes" else 10)


@pytest.mark.lento
@pytest.mark.parametrize("conjunto", ["treino", "teste", "producao"])
def test_linha_base_reproduz_contagens_e_modelo_trivial(conjunto: str) -> None:
    """As métricas salvas devem corresponder às mesmas decisões e aos mesmos alvos."""
    resumo = pd.read_csv(RAIZ / "resultados/linha_base.csv")
    for modo in ("rotulado", "sem_alvo"):
        previsoes = pd.read_csv(RAIZ / f"resultados/previsoes_{conjunto}_{modo}.csv")
        for versao in ("v1", "v2"):
            linha = resumo.loc[
                (resumo["conjunto"] == conjunto)
                & (resumo["modo"] == modo)
                & (resumo["versao"] == versao)
            ].iloc[0]
            alvo = previsoes["falha_72h"]
            decisao = previsoes[f"predicao_{versao}"]
            for nome, valor in sn.avaliacao.metricas(alvo, decisao).items():
                assert linha[nome] == pytest.approx(valor)
            assert linha["vp"] + linha["fn"] == alvo.sum()
            assert linha["acuracia_trivial"] == pytest.approx(1 - alvo.mean())


@pytest.mark.lento
@pytest.mark.parametrize("conjunto", ["teste", "producao"])
def test_comparacao_real_reproduz_intervalos_salvos(conjunto: str) -> None:
    """Recalcula o bootstrap real e confere o sinal v2 menos v1 de cada métrica."""
    previsoes = pd.read_csv(RAIZ / f"resultados/previsoes_{conjunto}_sem_alvo.csv")
    calculado = comparar_pareado(previsoes)
    salvo = pd.read_csv(RAIZ / "resultados/comparacao_pareada.csv")
    esperado = salvo.loc[
        (salvo["conjunto"] == conjunto) & (salvo["modo"] == "sem_alvo"),
        calculado.columns,
    ].reset_index(drop=True)
    pd.testing.assert_frame_equal(calculado, esperado, atol=1e-12, rtol=1e-12)
    np.testing.assert_allclose(
        calculado["diferenca_v2_v1"],
        calculado["v2"] - calculado["v1"],
    )
    assert (calculado["ic_inferior"] <= calculado["ic_superior"]).all()
