"""Fixtures independentes; cada teste recebe cópias ou objetos recém-criados."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn


@pytest.fixture
def lote_real() -> pd.DataFrame:
    """Carrega o conjunto de teste sem alterar o objeto entre testes."""
    return sn.dados.carregar("teste")


@pytest.fixture
def lote_controlado() -> pd.DataFrame:
    """Fornece 48 leituras horárias válidas, constantes e sem alvo."""
    quantidade = 48
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-06-01", periods=quantidade, freq="h"),
            "id_maquina": "M01",
            "idade_equipamento_meses": 60,
            "id_operador": "OP-01",
            "turno": 1,
            "temperatura_c": 60.0,
            "vibracao_rms": 2.0,
            "pressao": 3.5,
            "unidade_pressao": "bar",
            "corrente_a": 18.0,
            "rpm": 1700.0,
            "horas_operacao": np.full(quantidade, 100.0),
        }
    )


@pytest.fixture
def features_reais(lote_real: pd.DataFrame) -> pd.DataFrame:
    """Produz features sem disponibilizar os rótulos à inferência."""
    return sn.features.construir(
        sn.preprocessamento.limpar(lote_real.drop(columns="falha_72h"))
    )
