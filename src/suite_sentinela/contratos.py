"""Contratos extraídos da ficha de sensores e inventário independente da origem."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

FAIXAS = {
    "temperatura_c": (45.0, 95.0),
    "vibracao_rms": (1.2, 8.0),
    "pressao": (3.0, 4.5),
    "corrente_a": (12.0, 30.0),
    "rpm": (1650.0, 1800.0),
    "idade_equipamento_meses": (6.0, 180.0),
}
FATOR_PSI = 14.5038
RAIZ = Path(__file__).resolve().parents[2]
ORIGEM = RAIZ.parent / "sentinela-nortemec"


def pressao_em_bar(quadro: pd.DataFrame) -> pd.Series:
    """Converte somente para auditoria, sem substituir entradas do Sentinela."""
    unidades = quadro["unidade_pressao"].str.strip().str.lower()
    if not unidades.isin(["bar", "psi"]).all():
        raise ValueError("Unidade de pressão desconhecida")
    return (
        quadro["pressao"]
        .astype(float)
        .where(
            unidades == "bar",
            quadro["pressao"].astype(float) / FATOR_PSI,
        )
    )


def inventariar_origem() -> list[dict[str, str | int]]:
    """Registra todos os arquivos, incluindo controle de versão, sem chamar Git."""
    registros: list[dict[str, str | int]] = []
    for caminho in sorted(ORIGEM.rglob("*")):
        if caminho.is_file():
            registros.append(
                {
                    "caminho": caminho.relative_to(ORIGEM).as_posix(),
                    "bytes": caminho.stat().st_size,
                    "sha256": hashlib.sha256(caminho.read_bytes()).hexdigest(),
                }
            )
    return registros


def verificar_origem() -> dict[str, object]:
    """Compara nomes, tamanhos e hashes com o estado inicial preservado."""
    anterior = json.loads(
        (RAIZ / "evidencias/estado_original.json").read_text(
            encoding="utf-8-sig",
        )
    )
    atual = inventariar_origem()
    por_nome_anterior = {registro["caminho"]: registro for registro in anterior}
    por_nome_atual = {registro["caminho"]: registro for registro in atual}
    divergencias = sorted(
        nome
        for nome in por_nome_anterior.keys() | por_nome_atual.keys()
        if por_nome_anterior.get(nome) != por_nome_atual.get(nome)
    )
    return {
        "arquivos_antes": len(anterior),
        "arquivos_depois": len(atual),
        "divergencias": divergencias,
        "inalterado": not divergencias,
    }
