"""Oráculos analíticos e metamórficos para as 13 features e o histórico temporal."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn

pytestmark = pytest.mark.rapido


def test_treze_features_em_lote_constante(lote_controlado: pd.DataFrame) -> None:
    """O caso constante fornece um oráculo fechado para todas as colunas."""
    obtido = sn.features.construir(lote_controlado)
    esperado = [60, 60, 0, 2, 2, 18, 3.5, 1700, 60, 100, 0.108631, 0, 1]
    assert tuple(obtido.columns) == sn.features.ORDEM_FEATURES
    assert obtido.shape == (48, 13)
    np.testing.assert_allclose(obtido, np.tile(esperado, (48, 1)), atol=1e-12)


def test_embaralhamento_preserva_identidade_e_valores(
    lote_controlado: pd.DataFrame,
) -> None:
    """Reordenação do mesmo histórico só deve reordenar a saída."""
    lote_controlado["temperatura_c"] = np.linspace(50, 90, len(lote_controlado))
    embaralhado = lote_controlado.sample(frac=1, random_state=42)
    obtido = sn.features.construir(embaralhado)
    esperado = sn.features.construir(lote_controlado).loc[embaralhado.index]
    pd.testing.assert_frame_equal(obtido, esperado)


def test_janelas_nao_misturam_motores(lote_controlado: pd.DataFrame) -> None:
    """Leituras de outro motor não alteram as janelas do primeiro."""
    outro = lote_controlado.assign(id_maquina="M02", temperatura_c=90, vibracao_rms=7)
    junto = pd.concat([lote_controlado, outro], ignore_index=True)
    obtido = sn.features.construir(junto).iloc[:48]
    pd.testing.assert_frame_equal(obtido, sn.features.construir(lote_controlado))


def test_janelas_passadas_e_delta_24h(lote_controlado: pd.DataFrame) -> None:
    """Pulsos com posição conhecida verificam limites de 6, 24 e deslocamento 24."""
    lote_controlado.loc[0, ["temperatura_c", "vibracao_rms", "corrente_a"]] = [
        84,
        8,
        30,
    ]
    obtido = sn.features.construir(lote_controlado)
    assert obtido.loc[5, "vib_media_6h"] == pytest.approx(3)
    assert obtido.loc[6, "vib_media_6h"] == pytest.approx(2)
    assert obtido.loc[5, "corrente_media_6h"] == pytest.approx(20)
    assert obtido.loc[23, "temp_max_24h"] == 84
    assert obtido.loc[24, "temp_max_24h"] == 60
    assert obtido.loc[24, "delta_temp_24h"] == -24
    assert obtido.loc[24, "vib_max_24h"] == 2


@pytest.mark.defeito
def test_leituras_futuras_nao_alteram_feature_passada(
    lote_controlado: pd.DataFrame,
) -> None:
    """Modificar t=11 não pode alterar a feature de temperatura em t=10."""
    alterado = lote_controlado.copy()
    alterado.loc[11, "temperatura_c"] = 90
    original = sn.features.construir(lote_controlado).loc[10, "temp_media_6h"]
    obtido = sn.features.construir(alterado).loc[10, "temp_media_6h"]
    assert obtido == pytest.approx(original), (
        f"Passado mudou de {original} para {obtido}"
    )


@pytest.mark.defeito
def test_alvo_futuro_nao_altera_risco_passado(lote_controlado: pd.DataFrame) -> None:
    """Rótulos das 24 últimas leituras não devem modificar a primeira feature."""
    lote_controlado["falha_72h"] = 0
    alterado = lote_controlado.copy()
    alterado.loc[24:, "falha_72h"] = 1
    original = sn.features.construir(lote_controlado).loc[0, "maquina_risco"]
    obtido = sn.features.construir(alterado).loc[0, "maquina_risco"]
    assert obtido == pytest.approx(original), f"Risco passado: {original} -> {obtido}"


@pytest.mark.defeito
def test_recorte_com_historico_suficiente_independe_do_futuro(
    lote_controlado: pd.DataFrame,
) -> None:
    """O prefixo inclui todo o passado; diferenças não são falta de aquecimento."""
    lote_controlado["temperatura_c"] = np.linspace(50, 90, 48)
    completo = sn.features.construir(lote_controlado)
    recorte = sn.features.construir(lote_controlado.iloc[:32])
    np.testing.assert_allclose(recorte.loc[31], completo.loc[31], atol=1e-12)


@pytest.mark.parametrize("quantidade", [1, 48])
def test_um_motor_e_linha_unica_sao_deterministicos(
    lote_controlado: pd.DataFrame,
    quantidade: int,
) -> None:
    """Sem histórico, o caso constante ainda possui expectativa conhecida."""
    entrada = lote_controlado.iloc[:quantidade]
    primeiro = sn.features.construir(entrada)
    segundo = sn.features.construir(entrada)
    pd.testing.assert_frame_equal(primeiro, segundo)
    assert primeiro.shape == (quantidade, 13)
    assert primeiro["temp_media_6h"].eq(60).all()


def test_features_exigem_campos_documentados(lote_controlado: pd.DataFrame) -> None:
    """A ausência de temperatura é rejeitada antes da construção de janelas."""
    with pytest.raises(ValueError, match="colunas ausentes"):
        sn.features.construir(lote_controlado.drop(columns="temperatura_c"))
