# Levantamento inicial — 13/09/2026

Consultei as fontes entregues posteriormente nos caminhos externos
autorizados para leitura, sem incluir os documentos no projeto.
Neste documento, registro somente a inspeção
que realizei; não constitui o relatório final nem evidência de execução de testes.

## Fontes lidas

Li integralmente, no repositório Sentinela, README.md,
guia-do-aluno.md, pyproject.toml, requirements.txt, conftest.py,
os oito módulos de src/sentinela e exemplos/test_exemplo.py.
Confrontei o manifesto com os seis arquivos que referencia: todos os
hashes conferem. Carreguei os CSVs para o inventário estrutural inicial.
Na inspeção estrutural dos modelos, identifiquei 60 árvores e 8.412 nós na v1;
80 árvores e 24.428 nós na v2. Os vetores de cada árvore têm comprimentos
consistentes e as probabilidades armazenadas pertencem a [0, 1]. Isso ainda
não valida as previsões nem a qualidade dos modelos. Li o script de treinamento,
sem executá-lo.

Consultei diretamente o arquivo projeto_final_trilha1.pdf e os materiais das aulas,
fornecidos posteriormente. A relação e a interpretação normativa
estão em `fontes_normativas.md`. O arquivo 00-material-de-consulta.md, citado
pelo guia, não integra os anexos; a bibliografia da aula 6 está disponível.

## Evidências disponíveis

- `../evidencias/estado_original.json`: caminhos, tamanhos e SHA-256 dos
  54 arquivos encontrados no Sentinela, incluindo arquivos de controle Git.
- `../evidencias/verificacao_manifesto.json`: hashes esperados e obtidos dos
  três conjuntos, dos dois modelos e da tabela de risco.
- `../evidencias/inventario_dados.json`: contagens, colunas, positivos,
  ausências de vibração e unidades de pressão encontradas por conjunto.
- `../evidencias/verificacao_estado.json`: comparação com o estado inicial.

Até esta etapa do levantamento, não executei comandos Git nem escrevi no Sentinela.

## Hipóteses para testes executáveis

| Origem | Observação no código | Experimento necessário |
|---|---|---|
| features.construir | A média de temperatura utiliza `center=True`. | Alterar somente leituras futuras e verificar a invariância das features passadas. |
| features._risco_por_maquina | A presença de falha_72h aciona a média do alvo no próprio lote. | Alterar somente os alvos e comparar features e inferência; comparar lote rotulado e sem alvo. |
| Modelo.prever_registro | O vetor é construído com registro.values(). | Permutar a inserção das mesmas chaves e comparar com a inferência tabular canônica. |
| preprocessamento.limpar | Ausências de vibração recebem zero, abaixo da faixa operacional declarada. | Isolar dropout e medir consequências sobre features e decisões. |
| preprocessamento.limpar | A unidade de pressão é normalizada textualmente; não há conversão numérica nesse módulo. | Comparar a mesma pressão física representada em bar e psi ao longo do pipeline. |

Essas observações não quantificam defeitos nem substituem testes executados.
Na comparação de recortes, deverei controlar o histórico necessário às janelas;
não tratarei automaticamente diferenças por ausência de histórico como bugs.
Na análise estatística, deverei considerar dependência temporal e agrupamento por
motor. Associação de operador com falha não demonstra causalidade.

## Ambiente confirmado

Ubuntu já estava instalado em WSL 2. A consulta inicial, executada sob outro
contexto de usuário, não enxergava o registro dessa distribuição. Ao verificar
no contexto correto, confirmei a instalação existente; não instalei nenhuma distribuição
nova. Utilizo Python 3.14.4 e uma .venv exclusiva desta suíte.

O vínculo instalável que preparei em scripts/preparar_dependencia.py preserva a
resolução de dados e artefatos no diretório original, sem executar build nele.
PYTHONDONTWRITEBYTECODE impede bytecode na origem. A captura do pytest usa
memória, evitando uma incompatibilidade que observei com arquivos temporários
de captura na montagem /mnt/c. Os três exemplos passaram nessa configuração.
