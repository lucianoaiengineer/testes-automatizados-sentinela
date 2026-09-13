"""Verifica o detector com identidade e mudança de forma sem mudança de média."""

import numpy as np
import pandas as pd
import pytest

from suite_sentinela.distribuicoes import ajustar_holm, comparar_distribuicao

pytestmark = pytest.mark.rapido


def test_forma_muda_mesmo_com_media_igual() -> None:
    """Amostras simétricas com dispersões diferentes isolam o efeito de forma."""
    motores = np.repeat([f"M{i}" for i in range(12)], 20)
    teste = pd.DataFrame({"id_maquina": motores, "valor": np.tile([-1.0, 1.0], 120)})
    producao = teste.assign(valor=np.tile([-4.0, 4.0], 120))
    resumo = comparar_distribuicao(teste, producao, "valor", repeticoes=999)
    assert resumo["diferenca_media"] == 0
    assert resumo["ks"] == 0.5
    assert float(resumo["p_permutacao_motor"]) < 0.01
    assert float(resumo["variancia_producao"]) > float(resumo["variancia_teste"])
    identidade = comparar_distribuicao(teste, teste, "valor", repeticoes=99)
    assert identidade["ks"] == 0 and identidade["p_permutacao_motor"] == 1
    assert identidade["wasserstein"] == 0


def test_ajuste_holm_preserva_ordem_e_controla_multiplicidade() -> None:
    """Exemplo numérico fechado verifica a ordenação e o máximo acumulado."""
    np.testing.assert_allclose(
        ajustar_holm(np.array([0.04, 0.01, 0.03])), [0.06, 0.03, 0.06]
    )
    np.testing.assert_array_equal(ajustar_holm(np.array([])), np.array([]))


def test_constantes_distintas_nao_possuem_efeito_padronizado_finito() -> None:
    """Dispersão nula não pode transformar uma diferença real em efeito zero."""
    teste = pd.DataFrame({"id_maquina": ["A", "B"], "valor": [1.0, 1.0]})
    producao = teste.assign(valor=2.0)
    resumo = comparar_distribuicao(teste, producao, "valor", repeticoes=9)
    assert resumo["diferenca_media"] == 1
    assert np.isnan(float(resumo["diferenca_padronizada"]))


@pytest.mark.parametrize("valores", [[np.nan], [-0.1], [1.1], [[0.2]]])
def test_holm_rejeita_p_valores_invalidos(valores: list) -> None:
    """Valores fora do domínio de probabilidades não são corrigíveis."""
    with pytest.raises(ValueError):
        ajustar_holm(np.array(valores))


@pytest.mark.parametrize(
    "caso", ["vazio", "infinito", "motores", "ausente", "repeticoes"]
)
def test_distribuicoes_rejeitam_comparacoes_invalidas(caso: str) -> None:
    """Impede diagnóstico quando falta suporte para o teste por motor."""
    teste = pd.DataFrame(
        {"id_maquina": ["A", "A", "B", "B"], "valor": [1.0, 2.0, 3.0, 4.0]}
    )
    producao = teste.copy()
    if caso == "vazio":
        producao = producao.iloc[:0]
    elif caso == "infinito":
        producao["valor"] = np.inf
    elif caso == "motores":
        producao["id_maquina"] = "C"
    elif caso == "ausente":
        producao.loc[producao["id_maquina"] == "A", "valor"] = np.nan
    with pytest.raises(ValueError):
        comparar_distribuicao(
            teste, producao, "valor", repeticoes=0 if caso == "repeticoes" else 9
        )
