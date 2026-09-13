"""Contrafactuais administrativos separados de evidência causal."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn

from suite_sentinela.adversarial import medir_mudanca

pytestmark = pytest.mark.lento


@pytest.mark.parametrize(
    "campo,primeiro,segundo", [("id_operador", "OP-01", "OP-07"), ("turno", 1, 3)]
)
@pytest.mark.parametrize("versao", ["v1", "v2"])
def test_contrafactual_administrativo_mantem_estado_fisico(
    lote_real: pd.DataFrame,
    campo: str,
    primeiro: str | int,
    segundo: str | int,
    versao: str,
) -> None:
    """Isola a intervenção; o efeito medido não prova ilegitimidade causal."""
    entrada = lote_real.drop(columns="falha_72h")
    antes = entrada.assign(**{campo: primeiro})
    depois = entrada.assign(**{campo: segundo})
    pd.testing.assert_frame_equal(antes.drop(columns=campo), depois.drop(columns=campo))
    probabilidade_antes = sn.pipeline.executar(antes, versao=versao)[
        "probabilidade"
    ].to_numpy()
    probabilidade_depois = sn.pipeline.executar(depois, versao=versao)[
        "probabilidade"
    ].to_numpy()
    resumo = medir_mudanca(probabilidade_antes, probabilidade_depois)
    assert resumo["mudancas"] == np.count_nonzero(
        (probabilidade_antes >= 0.5) != (probabilidade_depois >= 0.5)
    )


def test_formatacao_do_operador_nao_altera_decisao(lote_real: pd.DataFrame) -> None:
    """Alterar só caixa e espaços preserva a identidade administrativa."""
    entrada = lote_real.drop(columns="falha_72h")
    alterado = entrada.copy()
    alterado["id_operador"] = " " + alterado["id_operador"].str.lower() + " "
    original = sn.pipeline.executar(entrada)
    comparado = sn.pipeline.executar(alterado)
    pd.testing.assert_frame_equal(original, comparado)
