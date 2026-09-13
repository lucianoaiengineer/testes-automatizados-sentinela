"""Inferência tabular, limiar inclusivo e contrato de dicionários de features."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn

pytestmark = pytest.mark.rapido


@pytest.mark.parametrize("versao", ["v1", "v2"])
def test_probabilidades_decisoes_ordem_e_determinismo(
    features_reais: pd.DataFrame,
    versao: str,
) -> None:
    """A ordem das colunas tabulares não deve modificar as previsões."""
    modelo = sn.modelo.carregar(versao)
    probabilidades = modelo.prever_proba(features_reais)
    assert modelo.versao == versao
    assert modelo.ordem_features == sn.features.ORDEM_FEATURES
    assert probabilidades.shape == (len(features_reais),)
    assert np.isfinite(probabilidades).all()
    assert ((probabilidades >= 0) & (probabilidades <= 1)).all()
    np.testing.assert_array_equal(probabilidades, modelo.prever_proba(features_reais))
    np.testing.assert_array_equal(
        probabilidades,
        modelo.prever_proba(features_reais.iloc[:, ::-1]),
    )
    np.testing.assert_array_equal(modelo.prever(features_reais), probabilidades >= 0.5)


@pytest.mark.parametrize(
    "limiar,esperado", [(0.5, 1), (0.50000001, 0), (0.49999999, 1)]
)
def test_limiar_exatamente_no_limite(limiar: float, esperado: int) -> None:
    """Uma folha controlada de probabilidade 0,5 isola o operador de decisão."""
    modelo = sn.modelo.Modelo(
        {
            "versao": "controle",
            "ordem_features": list(sn.features.ORDEM_FEATURES),
            "arvores": [
                {
                    "feature": [0],
                    "limiar": [0],
                    "filho_esq": [-1],
                    "filho_dir": [-1],
                    "prob": [0.5],
                }
            ],
        }
    )
    assert modelo.prever(np.zeros((1, 13)), limiar=limiar).tolist() == [esperado]


@pytest.mark.parametrize("valor", [np.nan, np.inf, -np.inf, "invalido"])
def test_modelo_rejeita_valores_invalidos(valor: object) -> None:
    """Features não finitas ou não numéricas não podem chegar à árvore."""
    entrada = np.ones((1, 13), dtype=object)
    entrada[0, 0] = valor
    with pytest.raises((ValueError, TypeError)):
        sn.modelo.carregar("v1").prever_proba(entrada)


@pytest.mark.parametrize("forma", [(13,), (1, 12), (1, 14), (1, 1, 13)])
def test_modelo_rejeita_forma_invalida(forma: tuple[int, ...]) -> None:
    """A entrada matricial exige exatamente duas dimensões e 13 colunas."""
    with pytest.raises(ValueError, match="esperado"):
        sn.modelo.carregar("v1").prever_proba(np.ones(forma))


@pytest.mark.parametrize("versao", ["v1", "v2"])
def test_registro_canonico_equivale_ao_lote(
    features_reais: pd.DataFrame, versao: str
) -> None:
    """O atalho de registro recebe features, não um dicionário de sensores crus."""
    modelo = sn.modelo.carregar(versao)
    registro = features_reais.iloc[0].to_dict()
    assert modelo.prever_registro(registro) == modelo.prever(features_reais.iloc[:1])[0]


@pytest.mark.parametrize("acao", ["remover", "adicionar", "tipo"])
def test_registro_rejeita_cardinalidade_ou_tipo_invalido(
    features_reais: pd.DataFrame,
    acao: str,
) -> None:
    """Campos em quantidade incorreta e tipos inválidos precisam ser rejeitados."""
    registro = dict(features_reais.iloc[0])
    if acao == "remover":
        registro.pop("pressao")
    elif acao == "adicionar":
        registro["extra"] = 0
    else:
        registro["pressao"] = "invalido"
    with pytest.raises((ValueError, TypeError)):
        sn.modelo.carregar("v1").prever_registro(registro)


@pytest.mark.defeito
def test_registro_rejeita_chave_substituida(features_reais: pd.DataFrame) -> None:
    """Ter 13 valores não basta quando uma feature obrigatória está ausente."""
    registro = features_reais.iloc[0].to_dict()
    registro["campo_desconhecido"] = registro.pop("turno")
    with pytest.raises(ValueError):
        sn.modelo.carregar("v1").prever_registro(registro)


@pytest.mark.defeito
@pytest.mark.parametrize("versao", ["v1", "v2"])
def test_registro_independe_da_ordem_de_insercao(
    features_reais: pd.DataFrame,
    versao: str,
) -> None:
    """Os mesmos nomes e valores devem produzir decisões idênticas."""
    modelo = sn.modelo.carregar(versao)
    amostra = features_reais.iloc[:100]
    canonicas = modelo.prever(amostra)
    invertidas = [
        modelo.prever_registro(dict(reversed(list(linha.items()))))
        for linha in amostra.to_dict(orient="records")
    ]
    mudancas = int(np.sum(canonicas != invertidas))
    assert mudancas == 0, f"{mudancas}/100 decisões mudaram só pela ordem das chaves"


def test_dataframe_exige_features_e_aceita_coluna_adicional(
    features_reais: pd.DataFrame,
) -> None:
    """Campos adicionais tabulares são ignorados; features ausentes são rejeitadas."""
    modelo = sn.modelo.carregar("v1")
    with pytest.raises(ValueError, match="features ausentes"):
        modelo.prever(features_reais.drop(columns="pressao"))
    np.testing.assert_array_equal(
        modelo.prever(features_reais),
        modelo.prever(features_reais.assign(extra=123)),
    )


def test_versao_inexistente_e_rejeitada() -> None:
    """O carregador só aceita as duas versões publicadas."""
    with pytest.raises(ValueError, match="versão desconhecida"):
        sn.modelo.carregar("v3")
