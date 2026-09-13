"""Jornada ponta a ponta, metadados, limiar e entradas fisicamente inválidas."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn


@pytest.mark.lento
@pytest.mark.parametrize("versao", ["v1", "v2"])
def test_pipeline_preserva_identidade_alvo_e_decisao(
    lote_real: pd.DataFrame,
    versao: str,
) -> None:
    """Confere metadados e concordância de etapas sobre as mesmas leituras."""
    entrada_original = lote_real.copy(deep=True)
    saida = sn.pipeline.executar(lote_real, versao=versao)
    limpo = sn.preprocessamento.limpar(lote_real)
    pd.testing.assert_frame_equal(lote_real, entrada_original)
    assert list(saida.columns) == [
        "id_maquina",
        "timestamp",
        "probabilidade",
        "predicao",
        "falha_72h",
    ]
    pd.testing.assert_frame_equal(
        saida[["id_maquina", "timestamp", "falha_72h"]],
        limpo[["id_maquina", "timestamp", "falha_72h"]],
    )
    np.testing.assert_allclose(
        saida["probabilidade"],
        sn.modelo.carregar(versao).prever_proba(sn.features.construir(limpo)),
    )
    np.testing.assert_array_equal(saida["predicao"], saida["probabilidade"] >= 0.5)
    assert saida["predicao"].nunique() == 2


@pytest.mark.rapido
def test_pipeline_limiar_inclusivo_e_sem_alvo(lote_controlado: pd.DataFrame) -> None:
    """Igualdade ao limiar também é inclusiva no caminho ponta a ponta."""
    primeira = sn.pipeline.executar(lote_controlado)
    limiar = float(primeira.loc[0, "probabilidade"])
    segunda = sn.pipeline.executar(lote_controlado, limiar=limiar)
    assert "falha_72h" not in segunda
    assert segunda.loc[0, "predicao"] == 1
    assert len(segunda) == 48


@pytest.mark.rapido
@pytest.mark.parametrize(
    "temperatura,vibracao,pressao,corrente,rpm,idade",
    [
        (45, 1.2, 3, 12, 1650, 6),
        (95, 8, 4.5, 30, 1800, 180),
    ],
)
def test_extremos_operacionais_validos_sao_processados(
    lote_controlado: pd.DataFrame,
    temperatura: float,
    vibracao: float,
    pressao: float,
    corrente: float,
    rpm: float,
    idade: int,
) -> None:
    """Os limites inclusivos da ficha são casos válidos do domínio de entrada."""
    entrada = lote_controlado.iloc[:1].assign(
        temperatura_c=temperatura,
        vibracao_rms=vibracao,
        pressao=pressao,
        corrente_a=corrente,
        rpm=rpm,
        idade_equipamento_meses=idade,
    )
    saida = sn.pipeline.executar(entrada)
    assert len(saida) == 1
    assert saida["probabilidade"].between(0, 1).all()
    assert saida.loc[0, "predicao"] == int(saida.loc[0, "probabilidade"] >= 0.5)


@pytest.mark.rapido
@pytest.mark.defeito
@pytest.mark.parametrize(
    "campo,valor",
    [
        ("temperatura_c", -274.0),
        ("vibracao_rms", -1.0),
        ("idade_equipamento_meses", -1),
    ],
)
def test_leitura_fisicamente_invalida_nao_gera_decisao(
    lote_controlado: pd.DataFrame,
    campo: str,
    valor: float,
) -> None:
    """Temperatura abaixo do zero absoluto, RMS e idade negativos são inválidos."""
    entrada = lote_controlado.iloc[:1].assign(**{campo: valor})
    try:
        saida = sn.pipeline.executar(entrada)
    except (ValueError, TypeError):
        return
    assert saida.empty, f"{campo}={valor} produziu {len(saida)} decisão sem rejeição"


@pytest.mark.rapido
def test_lote_constante_com_valores_repetidos_e_preservado(
    lote_controlado: pd.DataFrame,
) -> None:
    """Repetir valores físicos em horários distintos não é duplicar uma leitura."""
    saida = sn.pipeline.executar(lote_controlado)
    assert len(saida) == 48
    assert saida["timestamp"].nunique() == 48
    assert saida["probabilidade"].nunique() == 1
