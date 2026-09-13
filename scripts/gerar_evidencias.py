"""Executa a entrega e preserva resultados, falhas e verificação de integridade."""

from __future__ import annotations

import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import xml.etree.ElementTree as elementos
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LIMITE_COBERTURA_AUXILIAR = 95.0


def executar_comando(argumentos: list[str], nome_log: str) -> int:
    """Grava a saída integral em log local e devolve o código real do processo."""
    ambiente = os.environ.copy()
    ambiente.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": str(RAIZ / "src"),
            "TMPDIR": str(RAIZ / ".temporarios"),
            "PIP_NO_CACHE_DIR": "1",
        }
    )
    with (RAIZ / "evidencias" / nome_log).open("w", encoding="utf-8") as arquivo:
        resultado = subprocess.run(
            argumentos,
            cwd=RAIZ,
            env=ambiente,
            stdout=arquivo,
            stderr=subprocess.STDOUT,
            check=False,
        )
    print(f"status={resultado.returncode} evidencias/{nome_log}", flush=True)
    return resultado.returncode


def resumir_execucao(codigos: dict[str, int]) -> dict[str, object]:
    """Extrai resultados de JUnit e cobertura, sem transformar falhas em aprovações."""
    documento = elementos.parse(RAIZ / "evidencias/pytest.xml")
    casos = []
    for caso in documento.iter("testcase"):
        falha, erro, ignorado = (
            caso.find("failure"),
            caso.find("error"),
            caso.find("skipped"),
        )
        estado = "falhou" if falha is not None else "aprovado"
        if erro is not None:
            estado = "erro"
        if ignorado is not None:
            estado = "ignorado"
        casos.append(
            {
                "arquivo": caso.attrib["classname"].replace(".", "/") + ".py",
                "teste": caso.attrib["name"],
                "resultado": estado,
                "mensagem": falha.attrib.get("message", "")
                if falha is not None
                else "",
            }
        )
    cobertura = json.loads((RAIZ / "evidencias/cobertura.json").read_text())
    grupos: dict[str, dict[str, float]] = {}
    for nome, dados in cobertura["files"].items():
        grupo = "auxiliar" if "suite_sentinela" in nome else "sentinela"
        resumo = dados["summary"]
        acumulado = grupos.setdefault(grupo, {"cobertos": 0.0, "total": 0.0})
        acumulado["cobertos"] += resumo["covered_lines"] + resumo["covered_branches"]
        acumulado["total"] += resumo["num_statements"] + resumo["num_branches"]
    for resumo in grupos.values():
        resumo["percentual"] = 100 * resumo["cobertos"] / resumo["total"]
    return {
        "codigos": codigos,
        "casos": casos,
        "cobertura": grupos,
        "limite_cobertura_auxiliar": LIMITE_COBERTURA_AUXILIAR,
        "cobertura_auxiliar_atende": grupos["auxiliar"]["percentual"]
        >= LIMITE_COBERTURA_AUXILIAR,
        "python": platform.python_version(),
        "sistema": platform.system(),
        "dependencias": {
            nome: importlib.metadata.version(nome)
            for nome in (
                "sentinela",
                "numpy",
                "pandas",
                "scipy",
                "pytest",
                "pytest-cov",
                "ruff",
                "mypy",
            )
        },
    }


def gerar_evidencias() -> int:
    """Executa exemplos, análises e controles; retorna 1 se a suíte contém falhas.

    Ruff, mypy, exemplos ou análise com erro interrompem o fluxo. Falhas de
    contrato do Sentinela são mantidas no pytest e no código de saída final.
    """
    if Path(sys.prefix).resolve() != (RAIZ / ".venv").resolve():
        raise RuntimeError("Execute com o Python da .venv exclusiva deste projeto")
    (RAIZ / ".temporarios").mkdir(exist_ok=True)
    (RAIZ / "evidencias").mkdir(exist_ok=True)
    interpretador = [sys.executable, "-B"]
    etapas = {
        "exemplos": [
            *interpretador,
            "-m",
            "pytest",
            "-c",
            "pyproject.toml",
            "-p",
            "no:cacheprovider",
            "../sentinela-nortemec/exemplos",
            "-v",
        ],
        "linha_base": [*interpretador, "scripts/executar_linha_base.py"],
        "estatistica": [*interpretador, "scripts/executar_analise_estatistica.py"],
        "adversarial": [*interpretador, "scripts/executar_analise_adversarial.py"],
        "ruff": [*interpretador, "-m", "ruff", "check", "src", "scripts", "tests"],
        "mypy": [*interpretador, "-m", "mypy"],
    }
    codigos = {}
    for etapa, argumentos in etapas.items():
        codigos[etapa] = executar_comando(argumentos, f"{etapa}.log")
        if codigos[etapa] != 0:
            raise RuntimeError(f"Etapa {etapa} falhou; consulte o log")
    codigos["pytest"] = executar_comando(
        [
            *interpretador,
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "--cov=suite_sentinela",
            "--cov=sentinela",
            "--cov-report=term-missing",
            "--cov-report=json:evidencias/cobertura.json",
            "--junitxml=evidencias/pytest.xml",
        ],
        "pytest.log",
    )
    if codigos["pytest"] not in (0, 1):
        raise RuntimeError("Erro de execução do pytest; não é uma falha de contrato")
    resumo = resumir_execucao(codigos)
    (RAIZ / "evidencias/execucao.json").write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    # A importação fica após a configuração do ambiente dos subprocessos;
    # o comando de uso define PYTHONPATH para este processo também.
    from suite_sentinela.contratos import verificar_origem

    estado = verificar_origem()
    (RAIZ / "evidencias/verificacao_estado.json").write_text(
        json.dumps(estado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if not estado["inalterado"] or not resumo["cobertura_auxiliar_atende"]:
        raise RuntimeError("Verificação de integridade ou cobertura não atendida")
    return codigos["pytest"]


if __name__ == "__main__":
    raise SystemExit(gerar_evidencias())
