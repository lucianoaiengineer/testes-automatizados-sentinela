"""Ruído inferior à ficha do sensor e perturbação isolada das features."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn

from suite_sentinela.adversarial import (
    medir_mudanca,
    permutar_feature,
    perturbar_temperatura,
)


@pytest.mark.rapido
def test_medicao_de_mudancas_distingue_abertura_e_cancelamento() -> None:
    """Um exemplo fechado verifica denominadores e igualdade inclusiva a 0,5."""
    resumo = medir_mudanca(np.array([0.4, 0.6, 0.5]), np.array([0.5, 0.4, 0.5]))
    assert resumo["mudancas"] == 2
    assert resumo["taxa_mudanca"] == pytest.approx(2 / 3)
    assert resumo["ordens_abertas"] == resumo["ordens_canceladas"] == 1


@pytest.mark.lento
@pytest.mark.parametrize("versao", ["v1", "v2"])
@pytest.mark.parametrize("deslocamento", [-0.4, 0.4])
def test_ruido_termico_respeita_domino_e_mede_sensibilidade(
    lote_real: pd.DataFrame,
    versao: str,
    deslocamento: float,
) -> None:
    """Mede mudanças sem inventar uma taxa máxima aceitável para a manutenção."""
    entrada = lote_real.drop(columns="falha_72h")
    perturbado = perturbar_temperatura(entrada, deslocamento)
    pd.testing.assert_frame_equal(
        entrada.drop(columns="temperatura_c"), perturbado.drop(columns="temperatura_c")
    )
    assert (perturbado["temperatura_c"] - entrada["temperatura_c"]).abs().max() < 1
    original = sn.pipeline.executar(entrada, versao=versao)["probabilidade"].to_numpy()
    alterado = sn.pipeline.executar(perturbado, versao=versao)[
        "probabilidade"
    ].to_numpy()
    medicao = medir_mudanca(original, alterado)
    assert medicao["mudancas"] == int(np.sum((original >= 0.5) != (alterado >= 0.5)))
    assert (
        medicao["ordens_abertas"] + medicao["ordens_canceladas"] == medicao["mudancas"]
    )


@pytest.mark.rapido
@pytest.mark.parametrize("coluna", sn.features.ORDEM_FEATURES)
def test_permutacao_altera_apenas_uma_feature(
    features_reais: pd.DataFrame, coluna: str
) -> None:
    """A intervenção conserva a distribuição marginal, sem modificar outras colunas."""
    alterado = permutar_feature(features_reais, coluna)
    pd.testing.assert_frame_equal(
        features_reais.drop(columns=coluna), alterado.drop(columns=coluna)
    )
    np.testing.assert_array_equal(
        np.sort(features_reais[coluna]), np.sort(alterado[coluna])
    )
    pd.testing.assert_frame_equal(alterado, permutar_feature(features_reais, coluna))


@pytest.mark.rapido
@pytest.mark.parametrize("deslocamento", [0, 1, -1, np.inf])
def test_perturbacao_rejeita_magnitude_fora_do_ensaio(
    lote_controlado: pd.DataFrame,
    deslocamento: float,
) -> None:
    """O ensaio exige perturbação estritamente inferior ao ruído do sensor."""
    with pytest.raises(ValueError):
        perturbar_temperatura(lote_controlado, deslocamento)


@pytest.mark.rapido
def test_auxiliares_rejeitam_entradas_sem_significado(
    lote_controlado: pd.DataFrame,
) -> None:
    """Vetores desalinhados, valores inválidos e coluna inexistente são rejeitados."""
    for primeiro, segundo in (([], []), ([0.5], []), ([np.nan], [0.5]), ([1.1], [0.5])):
        with pytest.raises(ValueError):
            medir_mudanca(np.array(primeiro), np.array(segundo))
    with pytest.raises(ValueError):
        permutar_feature(lote_controlado, "inexistente")
    lote_controlado["temperatura_c"] = 200
    with pytest.raises(ValueError):
        perturbar_temperatura(lote_controlado, 0.4)
