"""Constrói um vínculo instalável com a origem, sem executar seu build.

O wheel contém somente metadados e um arquivo .pth apontando para src do
Sentinela. Assim, dados e artefatos continuam resolvidos na origem e nenhum
egg-info, cache ou arquivo de build precisa ser escrito no sistema sob teste.
Recrie o wheel após mover os repositórios; o vínculo utiliza caminho absoluto.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import tomllib
import zipfile
from pathlib import Path


def preparar_dependencia() -> Path:
    """Lê a configuração original e devolve o wheel local de vínculo.

    Levanta ValueError se nome, versão ou disposição do pacote divergirem
    da versão do Sentinela que esta suíte investiga.
    """
    raiz = Path(__file__).resolve().parents[1]
    origem = raiz.parent / "sentinela-nortemec"
    configuracao = tomllib.loads((origem / "pyproject.toml").read_text())
    projeto = configuracao["project"]
    if projeto["name"] != "sentinela" or projeto["version"] != "1.0.0":
        raise ValueError("Nome ou versão do Sentinela incompatível com a suíte")
    if not (origem / "src/sentinela/__init__.py").is_file():
        raise ValueError("Pacote Sentinela ausente na pasta irmã")
    metadados = "sentinela-1.0.0.dist-info"
    texto = (
        "Metadata-Version: 2.1\nName: sentinela\nVersion: 1.0.0\n"
        f"Requires-Python: {projeto['requires-python']}\n"
    )
    texto += "".join(
        f"Requires-Dist: {dependencia}\n" for dependencia in projeto["dependencies"]
    )
    arquivos = {
        "sentinela_origem.pth": (str(origem / "src") + "\n").encode(),
        f"{metadados}/METADATA": texto.encode(),
        f"{metadados}/WHEEL": (
            b"Wheel-Version: 1.0\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        ),
    }
    registro = io.StringIO(newline="")
    escritor = csv.writer(registro)
    for nome, conteudo in arquivos.items():
        resumo = base64.urlsafe_b64encode(hashlib.sha256(conteudo).digest())
        escritor.writerow(
            [nome, "sha256=" + resumo.decode().rstrip("="), len(conteudo)]
        )
    escritor.writerow([f"{metadados}/RECORD", "", ""])
    arquivos[f"{metadados}/RECORD"] = registro.getvalue().encode()
    destino = raiz / ".pacotes/sentinela-1.0.0-py3-none-any.whl"
    destino.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destino, "w") as pacote:
        for nome, conteudo in arquivos.items():
            pacote.writestr(zipfile.ZipInfo(nome), conteudo)
    return destino


if __name__ == "__main__":
    print(f"Dependência preparada: {preparar_dependencia()}")
