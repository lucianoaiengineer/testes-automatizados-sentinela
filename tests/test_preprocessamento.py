"""Contratos de limpeza, coerência física e unidades equivalentes."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn

pytestmark = pytest.mark.rapido


def test_limpeza_preserva_entrada_e_normaliza_rotulos(
    lote_controlado: pd.DataFrame,
) -> None:
    """Espaços e caixa são normalizados sem modificar o quadro fornecido."""
    lote_controlado["id_maquina"] = " m01 "
    lote_controlado["id_operador"] = " op-01 "
    lote_controlado["unidade_pressao"] = " BAR "
    original = lote_controlado.copy(deep=True)
    limpo = sn.preprocessamento.limpar(lote_controlado)
    pd.testing.assert_frame_equal(original, lote_controlado)
    assert set(limpo["id_maquina"]) == {"M01"}
    assert set(limpo["id_operador"]) == {"OP-01"}
    assert set(limpo["unidade_pressao"]) == {"bar"}
    assert pd.api.types.is_datetime64_any_dtype(limpo["timestamp"])
    assert pd.api.types.is_integer_dtype(limpo["turno"])


def test_limpeza_e_idempotente(lote_real: pd.DataFrame) -> None:
    """Limpar novamente não altera a representação já produzida."""
    limpo = sn.preprocessamento.limpar(lote_real)
    pd.testing.assert_frame_equal(limpo, sn.preprocessamento.limpar(limpo))


def test_motor_parado_e_descartado_com_ordem_preservada(
    lote_controlado: pd.DataFrame,
) -> None:
    """O descarte documentado explica exatamente a diferença de cardinalidade."""
    lote_controlado.loc[[0, 3], "rpm"] = 0
    limpo = sn.preprocessamento.limpar(lote_controlado)
    esperado = lote_controlado.drop(index=[0, 3])["timestamp"].reset_index(drop=True)
    pd.testing.assert_series_equal(limpo["timestamp"], esperado)
    assert len(limpo) == 46


@pytest.mark.defeito
def test_dropout_nao_se_converte_em_vibracao_fisicamente_invalida(
    lote_controlado: pd.DataFrame,
) -> None:
    """Um preenchimento numérico deve respeitar a faixa de 1,2–8 mm/s."""
    lote_controlado.loc[0, "vibracao_rms"] = np.nan
    obtido = sn.preprocessamento.limpar(lote_controlado).loc[0, "vibracao_rms"]
    assert 1.2 <= obtido <= 8.0, f"Dropout preenchido com {obtido} mm/s"


@pytest.mark.defeito
def test_pressao_equivalente_bar_psi_produz_mesma_feature(
    lote_controlado: pd.DataFrame,
) -> None:
    """Representações da mesma pressão não podem alterar a grandeza consumida."""
    em_psi = lote_controlado.copy()
    em_psi["pressao"] *= 14.5038
    em_psi["unidade_pressao"] = "psi"
    em_bar = sn.features.construir(sn.preprocessamento.limpar(lote_controlado))
    convertido = sn.features.construir(sn.preprocessamento.limpar(em_psi))
    np.testing.assert_allclose(convertido["pressao"], em_bar["pressao"], atol=1e-10)


@pytest.mark.parametrize("campo", ["timestamp", "turno", "idade_equipamento_meses"])
def test_tipo_nao_convertivel_e_rejeitado(
    lote_controlado: pd.DataFrame,
    campo: str,
) -> None:
    """Texto sem conversão possível não deve gerar uma leitura aparentemente válida."""
    lote_controlado[campo] = "invalido"
    with pytest.raises((ValueError, TypeError)):
        sn.preprocessamento.limpar(lote_controlado)
