# Testes automatizados do Sentinela

Projeto Final da Trilha 1 — ML clássico, disciplina Testes Automatizados para
Modelos de IA, IEC PUC Minas. **Entrega individual: Luciano Magalhães.**

Desenvolvi esta suíte externa para investigar dados, pré-processamento, features,
inferência, desempenho estatístico e robustez das versões v1 e v2. O Sentinela permanece
inalterado. Seus dados são sintéticos, conforme declarado no README original.

O relatório está em [relatorio.md](relatorio.md), as falhas em
[docs/falhas_encontradas.md](docs/falhas_encontradas.md) e a rastreabilidade em
[docs/matriz_requisitos.md](docs/matriz_requisitos.md). Consultei as fontes da disciplina
externamente; elas não fazem parte desta entrega.

## Ambiente e instalação

Desenvolvi e validei a suíte em Ubuntu via WSL 2, utilizando Python 3.14.4
e um ambiente virtual isolado. Para reproduzir a execução, abra a pasta do
projeto no VS Code conectado ao WSL e utilize o terminal Ubuntu. A instalação
inicial requer Python com suporte a `venv` e acesso ao índice de pacotes. Os
procedimentos descritos a seguir não modificam os arquivos originais do
Sentinela nem executam operações Git.

As duas pastas devem ser irmãs:
A suíte depende apenas dessa disposição relativa e não de um caminho absoluto específico.

```text
diretorio-de-trabalho/
├── sentinela-nortemec/
└── testes-automatizados-sentinela/
```

Em ambiente limpo, execute:

```bash
cd testes-automatizados-sentinela
mkdir -p .temporarios
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$PWD/.temporarios"
export PIP_NO_CACHE_DIR=1
python3 -m venv .venv
source .venv/bin/activate
python -B scripts/preparar_dependencia.py
python -B -m pip install --no-compile -r requirements-lock.txt
export PYTHONPATH="$PWD/src"
```

requirements-lock.txt fixa todas as versões observadas na execução. O arquivo
requirements.txt documenta as dependências diretas e intervalos compatíveis;
para reproduzir a entrega, use o arquivo fixado. O comando de criação do
ambiente é destinado a instalação nova: preserve a .venv já existente quando
retomar o trabalho na mesma instalação.

O script preparar_dependencia.py lê nome, versão e dependências do pyproject
original e cria um wheel local com metadados e vínculo .pth para o src original.
Assim, import sentinela utiliza os arquivos originais e seus caminhos de dados
e artefatos, sem executar build ou criar egg-info no Sentinela. Recrie esse
wheel ao mover as pastas; ele contém um caminho absoluto. A dependência local
não é substituída por um pacote homônimo do índice público.

O estado de referência está em evidencias/estado_original.json, incluindo
arquivos de controle de versão. A reprodução da auditoria completa requer a
mesma árvore original: outro checkout com conteúdo interno de .git diferente
pode passar no manifesto publicado e falhar na comparação de estado completo.
Não sobrescreva a referência para ocultar divergências.

## Execução completa

Com a .venv ativada e as variáveis acima definidas:

```bash
python -B scripts/gerar_evidencias.py
```

Esse comando executa os três exemplos, refaz a linha de base, as análises
estatística e adversarial, Ruff, mypy e pytest com cobertura. Grava logs
integrais em evidencias/ e mostra apenas status e caminhos no terminal.
**O código de saída esperado nesta versão é 1:** a suíte encontra falhas reais
do Sentinela. Os casos não usam xfail ou skip para transformar reprovação
em sucesso. Os resultados completos ficam em evidencias/pytest.xml e
evidencias/execucao.json, além do log textual.

Erros de análise, Ruff, mypy ou dos exemplos interrompem a execução e não são
classificados como defeitos do Sentinela. Defini o limite de cobertura dos auxiliares
em 95% após a primeira medição. No relatório, explico seu alcance.

## Execução por etapa

```bash
python -B -m pytest -c pyproject.toml -p no:cacheprovider ../sentinela-nortemec/exemplos -v > evidencias/exemplos.log 2>&1
python -B scripts/executar_linha_base.py > evidencias/linha_base.log 2>&1
python -B scripts/executar_analise_estatistica.py > evidencias/estatistica.log 2>&1
python -B scripts/executar_analise_adversarial.py > evidencias/adversarial.log 2>&1
python -B -m pytest -p no:cacheprovider > evidencias/pytest.log 2>&1
python -B -m ruff check src scripts tests > evidencias/ruff.log 2>&1
python -B -m mypy > evidencias/mypy.log 2>&1
```

Os testes que conferem os CSVs de resultados pressupõem a execução das análises
anteriores. Os resultados incluídos na entrega permitem consultar as evidências
sem nova execução. Para rodar somente partes da suíte:

```bash
python -B -m pytest -m rapido > evidencias/testes_rapidos.log 2>&1
python -B -m pytest -m lento > evidencias/testes_lentos.log 2>&1
python -B -m pytest -m defeito > evidencias/testes_defeitos.log 2>&1
```

O marcador defeito não cobre necessariamente todas as reprovações possíveis:
as validações parametrizadas dos CSVs também podem falhar. A execução sem
seleção é a referência da entrega. A configuração usa captura em memória
(`--capture=sys`), evitando problemas de captura por descritores na montagem
/mnt/c. PYTHONDONTWRITEBYTECODE impede bytecode no pacote original.

## Dependências e responsabilidades

| Componente | Finalidade |
|---|---|
| Sentinela local | Sistema sob teste; modelos JSON e dados originais |
| NumPy e pandas | Vetores, matrizes, alinhamento de leituras e tabelas |
| SciPy | KS e distância de Wasserstein |
| pytest e pytest-cov | Contratos executáveis, relatórios e cobertura de linhas/ramos |
| Ruff | Estilo, imports e erros estáticos no código autoral |
| mypy e pandas-stubs | Verificação de tipos autorais e das operações tabulares |

Não é necessário scikit-learn: não há treinamento. Os exemplos didáticos
das aulas não são dependências, dados de teste ou resultados do Sentinela.

## Organização

| Pasta/arquivo | Responsabilidade |
|---|---|
| tests/ | Dados, limpeza, features, modelo, estatística, calibração, distribuições, adversarial, contrafactual e pipeline |
| src/suite_sentinela/ | Contratos e cálculos auxiliares reutilizados pelos testes e análises |
| scripts/ | Instalação do vínculo, análises e execução reproduzível |
| resultados/ | Previsões, métricas, intervalos, calibração, limiares, distribuições e intervenções |
| evidencias/ | Estado inicial/final, logs, JUnit, cobertura e versões |
| docs/ | Fontes, metodologia, hipóteses, rastreabilidade e causas das falhas |
| relatorio.md | Interpretação dos resultados e recomendações |

Ampliei a separação em relação à estrutura básica do professor para
reutilizar os cálculos sem duplicar lógica entre testes e análise. Não há
módulo separado de contrafactuais: as intervenções usam os mesmos auxiliares
de comparação e a interface pública do Sentinela.

## Limites da entrega

Realizei uma avaliação externa e retrospectiva. Não realizei treinamento, correção do Sentinela, alteração de limiar ou implantação do sistema. As operações Git limitaram-se ao versionamento e à publicação desta suíte externa. O mesmo comando completo pode ser usado por um ambiente de
integração contínua que disponibilize a árvore original e a .venv; não
realizei execução remota. A integridade final confirma os mesmos 54 arquivos
e hashes da origem. O relatório deve ser revisto se dados, modelos ou
dependências mudarem.
