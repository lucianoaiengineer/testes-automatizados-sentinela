"""Inspeção dos três CSVs, suas chaves temporais e faixas físicas publicadas."""

import numpy as np
import pandas as pd
import pytest
import sentinela as sn

from suite_sentinela.contratos import FAIXAS, pressao_em_bar, verificar_origem

pytestmark = pytest.mark.lento


def test_manifesto_e_estado_original_conferem() -> None:
    """A análise não pode alterar nenhum arquivo do sistema sob teste."""
    assert sn.artefatos.verificar_manifest() == []
    assert verificar_origem()["inalterado"] is True


@pytest.mark.parametrize(
    "conjunto,quantidade", [("treino", 16800), ("teste", 4200), ("producao", 4200)]
)
def test_schema_completude_tipos_e_alvo(conjunto: str, quantidade: int) -> None:
    """Dropout de vibração é permitido; demais campos são obrigatórios."""
    bruto = sn.dados.carregar(conjunto)
    assert tuple(bruto.columns) == sn.dados.COLUNAS
    assert len(bruto) == quantidade
    assert bruto.drop(columns="vibracao_rms").notna().all().all()
    numericas = [*FAIXAS, "turno", "horas_operacao", "falha_72h"]
    for coluna in numericas:
        assert pd.api.types.is_numeric_dtype(bruto[coluna]), coluna
        assert np.isfinite(bruto[coluna].dropna()).all(), coluna
    assert bruto["falha_72h"].isin([0, 1]).all()
    assert bruto["turno"].isin([1, 2, 3]).all()
    assert bruto["horas_operacao"].ge(0).all()
    assert bruto["idade_equipamento_meses"].mod(1).eq(0).all()
    operadores = bruto["id_operador"].str.strip().str.upper()
    assert operadores.isin([f"OP-{numero:02d}" for numero in range(1, 13)]).all()
    maquinas = bruto["id_maquina"].str.strip().str.upper()
    assert maquinas.isin([f"M{numero:02d}" for numero in range(1, 26)]).all()


@pytest.mark.parametrize("conjunto", sn.dados.CONJUNTOS)
def test_chave_temporal_unica_e_cadencia_horaria(conjunto: str) -> None:
    """Uma leitura por motor por hora, sem duplicação da chave normalizada."""
    bruto = sn.dados.carregar(conjunto)
    bruto["timestamp"] = pd.to_datetime(bruto["timestamp"], errors="raise")
    bruto["id_maquina"] = bruto["id_maquina"].str.strip().str.upper()
    assert not bruto.duplicated(["id_maquina", "timestamp"]).any()
    assert not bruto.duplicated().any()
    assert bruto["id_maquina"].nunique() == 25
    for _, motor in bruto.groupby("id_maquina"):
        assert motor["timestamp"].is_monotonic_increasing
        diferencas = np.diff(motor["timestamp"].to_numpy(dtype="datetime64[ns]"))
        assert (diferencas == np.timedelta64(1, "h")).all()


def test_particoes_temporais_nao_se_sobrepoem() -> None:
    """As janelas consecutivas usam períodos distintos, embora compartilhem motores."""
    periodos = [
        pd.to_datetime(sn.dados.carregar(nome)["timestamp"])
        for nome in sn.dados.CONJUNTOS
    ]
    assert periodos[0].max() < periodos[1].min()
    assert periodos[1].max() < periodos[2].min()


@pytest.mark.parametrize("conjunto", sn.dados.CONJUNTOS)
@pytest.mark.parametrize("coluna", FAIXAS)
def test_faixas_operacionais_dos_dados(conjunto: str, coluna: str) -> None:
    """Conta violações no CSV, convertendo psi apenas para comparar grandezas."""
    bruto = sn.dados.carregar(conjunto)
    valores = pressao_em_bar(bruto) if coluna == "pressao" else bruto[coluna]
    minimo, maximo = FAIXAS[coluna]
    # Dropout é ausência conhecida, não uma leitura numérica fora da faixa.
    invalidos = ~valores.dropna().between(minimo, maximo)
    assert not invalidos.any(), (
        f"{conjunto}/{coluna}: {int(invalidos.sum())} fora da faixa"
    )


def test_nome_de_conjunto_invalido_e_rejeitado() -> None:
    """A interface não deve carregar caminhos arbitrários como conjuntos."""
    with pytest.raises(ValueError, match="conjunto desconhecido"):
        sn.dados.carregar("inexistente")
