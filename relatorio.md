# Relatório de avaliação externa do Sentinela

**Projeto Final — Trilha 1, ML clássico**  
**Disciplina:** Testes Automatizados para Modelos de IA — IEC PUC Minas  
**Entrega individual — Autor: Luciano Magalhães**  
**Data da avaliação:** 13/09/2026

Identifiquei sete grupos de defeitos, que reproduzi por meio de 15 testes que falham, entre 142 casos executados. Os outros 127 casos passaram. As evidências não sustentam promover a v2 somente pelo aumento de acurácia: há perda de recall e defeitos de preparação dos dados que comprometem a interpretação das métricas de ambas as versões. O Sentinela permaneceu integralmente inalterado.

## Escopo, fontes e procedimento

Avaliei os três blocos do enunciado: A, contratos de dados e pipeline; B, desempenho com incerteza, limiar, calibração e distribuições; C, perturbações, contrafactuais e limites. A [matriz de rastreabilidade](docs/matriz_requisitos.md) relaciona R01–R79 e 29 recomendações aplicáveis do guia a testes, evidências e interpretações.

O enunciado, o guia, o README, as configurações, os módulos, os exemplos, os dados e os artefatos originais fundamentam os contratos. Consultei os seis PDFs e 14 notebooks disponibilizados conforme o [registro de fontes](docs/fontes_normativas.md). Não copiei os anexos acadêmicos para esta entrega. A bibliografia mencionada nas aulas não é apresentada como leitura de artigos não fornecidos.

Utilizei exclusivamente a interface e os arquivos originais como sistema sob teste. Entradas controladas isolam propriedades; as análises de desempenho usam os CSVs publicados do Sentinela. Esses dados são **sintéticos segundo o README original**, embora os resultados apresentados sejam de execuções reais desses arquivos. Não representam validação em uma fábrica.

O inventário anterior ao desenvolvimento e sua comparação final registram 54 arquivos e nenhuma divergência de SHA-256, incluindo os arquivos de controle de versão. Os seis hashes do manifesto publicado também conferem. Evidências: [estado inicial](evidencias/estado_original.json), [manifesto](evidencias/verificacao_manifesto.json) e [estado final](evidencias/verificacao_estado.json). Na retomada, preservei os arquivos válidos já existentes na suíte.

## Dados e unidade de análise

| Conjunto | Leituras | Positivos | Prevalência | Vibração ausente | Acurácia trivial |
|---|---:|---:|---:|---:|---:|
| Treino | 16.800 | 1.939 | 11,54% | 1.217 | 88,46% |
| Teste | 4.200 | 655 | 15,60% | 408 | 84,40% |
| Produção | 4.200 | 599 | 14,26% | 353 | 85,74% |

Há 25 motores, cadência horária, chaves motor–timestamp únicas e partições temporalmente ordenadas sem sobreposição. As leituras publicadas permanecem após a limpeza; exercitei o filtro de motor parado em entrada controlada. A vibração ausente é prevista no dado, mas sua imputação deve continuar fisicamente coerente.

O alvo se refere à falha na janela de 72 horas. Portanto, leituras sucessivas não são eventos de falha independentes. VP, VN, FP e FN contam **leituras**, não motores distintos, falhas distintas ou ordens efetivamente emitidas. O classificador trivial prevê sempre zero: obtém a acurácia da última coluna, porém recall zero. Evidência: [inventário](evidencias/inventario_dados.json).

## Bloco A — contratos e comportamentos

Utilizei oráculos fechados para a matriz de confusão, calibração e vetor constante das 13 features; pulsos controlados para janelas e diferenças temporais; permutação de linhas com realinhamento por chave; comparação entre motores; equivalência física bar/psi; entradas inválidas; limiar exato; comparação de registro individual e lote; e execução ponta a ponta.

Entre os comportamentos que confirmei estão normalização de identificadores, idempotência e ausência de mutação da entrada na limpeza, filtragem de motor parado, separação dos motores, determinismo, ordem canônica de features no DataFrame, carregamento das duas versões, probabilidades válidas e decisões binárias. Exercitei entradas controladas com um motor, uma linha e valores repetidos. A ordem das chaves de um dicionário, contudo, viola o contrato de inferência individual.

### Falhas reproduzidas

| Grupo | Evidência medida | Causa identificada e consequência |
|---|---|---|
| F01 — futuro e recorte | Alterar temperatura futura de 60 para 90 °C muda a média anterior de 60 para 65; recorte e lote diferem em 0,8511 °C. Dois testes falham. | Janela centrada utiliza observações posteriores; resultado retrospectivo não reproduz disponibilidade online. |
| F02 — alvo na feature | Alterar somente alvos futuros muda o risco da primeira linha de 0 para 0,5. Um teste falha. | Risco por motor calculado com os alvos do lote; informação indisponível na previsão entra nas features. |
| F03 — unidade de pressão | 3,5 bar e 50,7633 psi geram features diferentes nas 48 linhas; diferença 47,2633. Um teste falha. | Ausência de conversão para unidade canônica; a mesma pressão física recebe representações distintas. |
| F04 — dropout | Vibração ausente vira 0,0 mm/s, abaixo de 1,2 mm/s. Um teste falha. | Imputação constante zero distorce o sinal e suas janelas. |
| F05 — contrato de registro | Inverter chaves muda 22/100 decisões da v1 e 12/100 da v2; substituir uma chave por desconhecida não é rejeitado. Três testes falham. | Uso posicional dos valores do dicionário sem validação nominal completa; previsão depende da construção do registro. |
| F06 — faixas publicadas | Treino: 5 pressões e 4 rotações fora da faixa; produção: 1 pressão e 1 rotação. Quatro testes parametrizados falham. | Dados publicados violam o contrato operacional; o gerador não foi fornecido para determinar a origem a montante. |
| F07 — entrada fisicamente inválida | Temperatura −274 °C, vibração RMS −1 e idade −1 produzem probabilidade e decisão zero. Três testes falham. | Validação física insuficiente permite inferência aparentemente válida para dados impossíveis. |

F06 representa violação da faixa declarada, que não equivale necessariamente a impossibilidade física. Em F07, o defeito é aceitar a entrada e produzir uma decisão; os exemplos não abriram manutenção. As hipóteses, funções executáveis, comandos de reprodução, valores, causas, impactos, riscos e recomendações de cada grupo estão em [falhas encontradas](docs/falhas_encontradas.md).

## Bloco B — desempenho e incerteza

### Linha de base

O limiar padrão é 0,5, incluindo igualdade. O modo `rotulado` reproduz a passagem do lote com alvo pelo pipeline; `sem_alvo` remove o alvo antes da construção de features e o usa apenas na avaliação externa. Essa separação mostra o efeito da dependência do alvo. **Sem alvo não significa sem vazamento temporal:** a janela centrada continua presente. O treino é diagnóstico retrospectivo, não estimativa de generalização.

| Conjunto / modo | Versão | VP | VN | FP | FN | Acurácia % | Precisão % | Recall % | F1 % |
|---|---|---|---|---|---|---|---|---|---|
| treino / rotulado | v1 | 1929 | 13520 | 1341 | 10 | 91,96 | 58,99 | 99,48 | 74,06 |
| treino / rotulado | v2 | 1744 | 14816 | 45 | 195 | 98,57 | 97,48 | 89,94 | 93,56 |
| treino / sem_alvo | v1 | 1929 | 13520 | 1341 | 10 | 91,96 | 58,99 | 99,48 | 74,06 |
| treino / sem_alvo | v2 | 1744 | 14816 | 45 | 195 | 98,57 | 97,48 | 89,94 | 93,56 |
| teste / rotulado | v1 | 617 | 3104 | 441 | 38 | 88,60 | 58,32 | 94,20 | 72,04 |
| teste / rotulado | v2 | 533 | 3334 | 211 | 122 | 92,07 | 71,64 | 81,37 | 76,20 |
| teste / sem_alvo | v1 | 614 | 2600 | 945 | 41 | 76,52 | 39,38 | 93,74 | 55,47 |
| teste / sem_alvo | v2 | 457 | 3112 | 433 | 198 | 84,98 | 51,35 | 69,77 | 59,16 |
| producao / rotulado | v1 | 587 | 3017 | 584 | 12 | 85,81 | 50,13 | 98,00 | 66,33 |
| producao / rotulado | v2 | 502 | 3135 | 466 | 97 | 86,60 | 51,86 | 83,81 | 64,07 |
| producao / sem_alvo | v1 | 566 | 2867 | 734 | 33 | 81,74 | 43,54 | 94,49 | 59,61 |
| producao / sem_alvo | v2 | 462 | 3137 | 464 | 137 | 85,69 | 49,89 | 77,13 | 60,59 |

Fonte: [linha de base completa](resultados/linha_base.csv), acompanhada das seis tabelas de previsões individuais em resultados/. No teste rotulado, a acurácia aumenta 3,48 pontos percentuais, mas os falsos negativos sobem de 38 para 122. Sem alvo, sobem de 41 para 198, enquanto os falsos positivos caem de 945 para 433. Assim, a v2 troca parte da sensibilidade por menos alarmes falsos. Na produção sem alvo, a mesma troca ocorre: FN 33→137 e FP 734→464.

Falsos positivos podem mobilizar inspeções desnecessárias; falsos negativos podem adiar uma intervenção necessária. O conjunto não fornece custos monetários, capacidade de manutenção ou recall mínimo aceitável. Não converti essas contagens em prejuízo financeiro nem escolhi uma versão com base em custo inventado.

### Comparação pareada

Utilizei 2.000 reamostragens dos 25 motores, com semente 42, mantendo juntas suas séries completas e as previsões pareadas das duas versões. Os intervalos percentis de 95% abaixo são marginais por métrica; não constituem garantia simultânea para todas as comparações.

| Modo (teste) | Métrica | Δ v2−v1 (pp) | IC 95% (pp) |
|---|---|---|---|
| rotulado | acuracia | 3,48 | [-1,19; 9,95] |
| rotulado | precisao | 13,32 | [0,25; 32,83] |
| rotulado | recall | -12,82 | [-24,44; -3,73] |
| rotulado | f1 | 4,16 | [-6,81; 17,34] |
| sem_alvo | acuracia | 8,45 | [-0,27; 18,10] |
| sem_alvo | precisao | 11,96 | [-0,32; 31,05] |
| sem_alvo | recall | -23,97 | [-40,53; -9,54] |
| sem_alvo | f1 | 3,69 | [-10,12; 17,40] |

O intervalo da diferença de acurácia no teste rotulado inclui zero; o ganho pontual não demonstra superioridade inequívoca. Os intervalos de recall ficam abaixo de zero nos dois modos de teste, indicando perda consistente nesse desenho de reamostragem. Intervalos de precisão e F1 precisam ser lidos separadamente: melhora pontual não garante melhora de toda métrica.

O agrupamento evita tratar milhares de horas como milhares de unidades independentes, mas pressupõe que motores sejam unidades adequadas para reamostragem. São apenas 25 motores; dependência entre motores, horizonte curto e dados sintéticos limitam extrapolação. Resultados de treino e produção também estão em [comparação pareada](resultados/comparacao_pareada.csv). Detalhes: [metodologia estatística](docs/metodologia_estatistica.md).

### Varredura de limiar

Avaliei 101 limiares entre 0 e 1, passo 0,01, em cada conjunto, modo e versão: 1.212 linhas de resultado. Seleção do teste sem alvo:

| Versão | Limiar | Precisão % | Recall % | FP | FN |
|---|---|---|---|---|---|
| v1 | 0,3 | 33,07 | 94,96 | 1259 | 33 |
| v1 | 0,5 | 39,38 | 93,74 | 945 | 41 |
| v1 | 0,7 | 49,37 | 71,30 | 479 | 188 |
| v2 | 0,3 | 44,37 | 86,56 | 711 | 88 |
| v2 | 0,5 | 51,35 | 69,77 | 433 | 198 |
| v2 | 0,7 | 76,79 | 45,95 | 91 | 354 |

Aumentar o limiar reduz o conjunto de positivos previstos e não aumenta recall; precisão não é necessariamente monotônica. Na v2, elevar 0,5 para 0,7 reduz FP de 433 para 91, mas aumenta FN de 198 para 354. Estes são pontos exploratórios da mesma amostra. Não ajustei o limiar do Sentinela. Uma escolha operacional exige política de custo e validação temporal independente, após resolver os vazamentos. Fonte: [varredura completa](resultados/varredura_limiar.csv).

### Calibração

Brier mede erro quadrático das probabilidades; ECE resume distância entre probabilidade média e frequência observada em dez faixas de mesma largura. Menor é melhor nestas medidas, mas ECE depende das faixas e pode ocultar desvios locais.

| Conjunto / modo | Versão | Brier | ECE |
|---|---|---|---|
| teste / rotulado | v1 | 0,0863 | 0,1355 |
| teste / rotulado | v2 | 0,0685 | 0,0716 |
| teste / sem_alvo | v1 | 0,1523 | 0,1906 |
| teste / sem_alvo | v2 | 0,0917 | 0,0576 |
| producao / rotulado | v1 | 0,0935 | 0,1400 |
| producao / rotulado | v2 | 0,0820 | 0,0823 |
| producao / sem_alvo | v1 | 0,1259 | 0,1693 |
| producao / sem_alvo | v2 | 0,0877 | 0,0717 |

Exemplo de teste sem alvo, mostrando que probabilidade não deve ser tomada automaticamente como frequência confiável:

| Versão / faixa | Leituras | Probabilidade média | Frequência observada |
|---|---:|---:|---:|
| v1 / [0,5; 0,6) | 219 | 55,77% | 20,55% |
| v1 / [0,9; 1,0] | 247 | 93,05% | 64,78% |
| v2 / [0,5; 0,6) | 220 | 54,54% | 28,64% |
| v2 / [0,9; 1,0] | 33 | 95,13% | 93,94% |

A v2 tem Brier e ECE menores nos cenários apresentados, porém sua faixa próxima ao limiar continua superestimando a frequência observada. A faixa alta com 33 leituras não demonstra calibração global. Não realizei recalibramento. Fontes: [resumo](resultados/calibracao_resumo.csv) e [todas as faixas](resultados/calibracao_faixas.csv).

### Distribuições entre teste e produção

Comparei as seis grandezas operacionais, horas de operação e turno. Converti pressão para bar apenas na auditoria, sem alterar o sistema. Variâncias amostrais usam ddof=1; Wasserstein conserva a unidade da variável.

| Variável | Média teste → produção | Variância teste → produção | KS | Wasserstein | p por motor |
|---|---|---|---|---|---|
| temperatura_c | 68,44 → 67,23 | 15,86 → 27,52 | 0,1338 | 1,5575 | 0,1540 |
| vibracao_rms | 3,13 → 3,06 | 0,58 → 0,63 | 0,1129 | 0,1126 | 0,5745 |
| pressao | 3,90 → 3,91 | 0,04 → 0,04 | 0,0564 | 0,0167 | 0,6495 |
| corrente_a | 19,82 → 19,72 | 1,84 → 2,01 | 0,0769 | 0,1566 | 0,6195 |
| rpm | 1756,89 → 1757,82 | 211,67 → 224,00 | 0,0588 | 1,2036 | 0,6765 |
| idade_equipamento_meses | 98,44 → 98,44 | 2722,33 → 2722,33 | 0,0000 | 0,0000 | 1,0000 |
| horas_operacao | 12568,30 → 12736,30 | 39203970,36 → 39203970,36 | 0,0514 | 168,0000 | 0,8770 |
| turno | 2,00 → 2,00 | 0,67 → 0,67 | 0,0000 | 0,0000 | 1,0000 |

Na temperatura, a média diminui 1,207 °C, mas a variância aumenta de 15,861 para 27,515 °C². O efeito médio padronizado é −0,259. Os quantis 1%/99% passam de 61,13/76,7602 para 56,03/79,0901 °C. Em produção, 15,95% das leituras ficam fora do intervalo entre p01 e p99 do teste. Portanto, olhar só a média perderia o alargamento das caudas.

O KS convencional da temperatura produz p≈3,53×10⁻³³, mas assume observações independentes; por isso, tratei esse resultado como exploratório. A análise por motor troca os períodos completos dentro de cada par, com 1.999 permutações, semente 42 e estatística de distância entre distribuições em grade comum de 201 quantis. Para temperatura, p=0,154. Após Holm sobre as oito variáveis, todos os p ajustados são 1,0.

Há mudanças descritivas de forma e cauda; o ensaio por motor não rejeita a hipótese nula após ajuste. Isso não comprova estabilidade ou equivalência. Sua potência é limitada e a permutação pressupõe permutabilidade dos períodos sob a hipótese nula. Horas de operação avançam 168 horas em média, efeito compatível com a passagem do tempo, não um defeito por si só. Vibração usa 3.792 e 3.847 observações não ausentes; analisei dropout separadamente.

Fontes: [distribuições e quantis](resultados/distribuicoes.csv), [categorias](resultados/distribuicoes_categoricas.csv) e metodologia. Turno é ordinal/categórico; sua distribuição de categorias complementa a estatística numérica.

## Bloco C — robustez, dependências e limites

### Perturbação térmica inferior ao ruído do sensor

Apliquei deslocamento sistemático de ±0,4 °C às leituras brutas, mantendo a faixa física e recalculando todo o pipeline sem alvo. A magnitude é inferior a 1 °C informado para o sensor. Trata-se de um ensaio de pequeno desvio do sensor, não de simulação de ruído aleatório independente.

| Conjunto | Versão | Δ temperatura °C | Mudanças / 4.200 | Taxa % | 0→1 | 1→0 |
|---|---|---|---|---|---|---|
| teste | v1 | -0.4 | 127 | 3,02 | 0 | 127 |
| teste | v1 | +0.4 | 104 | 2,48 | 104 | 0 |
| teste | v2 | -0.4 | 152 | 3,62 | 30 | 122 |
| teste | v2 | +0.4 | 155 | 3,69 | 133 | 22 |
| producao | v1 | -0.4 | 46 | 1,10 | 2 | 44 |
| producao | v1 | +0.4 | 56 | 1,33 | 55 | 1 |
| producao | v2 | -0.4 | 75 | 1,79 | 7 | 68 |
| producao | v2 | +0.4 | 50 | 1,19 | 49 | 1 |

Uma perturbação de +0,4 °C muda 155 decisões da v2 no teste: 133 de 0 para 1 e 22 de 1 para 0. A sensibilidade varia por conjunto e versão. Não estipulei um limite aceitável de mudanças sem contrato, nem exigi invariância a um sinal físico relevante. “Ordens abertas/canceladas” nos CSVs designa transições da decisão binária, não ações executadas em sistema de manutenção.

As probabilidades e linhas alteradas estão em [mudanças por leitura](resultados/mudancas_ruido.csv); contagens, magnitudes e deltas estão em [análise adversarial](resultados/adversarial.csv).

### Uma feature por vez

Realizei 52 permutações: 13 features × duas versões × dois conjuntos, com semente 42. Cada ensaio mantém as demais colunas intactas. No teste:

| Feature permutada | Mudanças v1 (%) | Mudanças v2 (%) |
|---|---|---|
| temp_media_6h | 18,57 | 13,64 |
| temp_max_24h | 9,40 | 9,88 |
| delta_temp_24h | 0,48 | 0,69 |
| vib_media_6h | 0,57 | 1,17 |
| vib_max_24h | 18,86 | 9,62 |
| corrente_media_6h | 4,50 | 4,60 |
| pressao | 0,55 | 2,24 |
| rpm | 0,67 | 1,52 |
| idade_equipamento_meses | 2,29 | 4,36 |
| horas_operacao | 5,83 | 6,31 |
| maquina_risco | 7,55 | 6,98 |
| operador_senior | 2,60 | 4,93 |
| turno | 0,05 | 0,19 |

Temperatura média e vibração máxima têm forte participação nas mudanças da v1. A v2 também depende do risco por máquina e do indicador de operador. A permutação pode romper correlações e criar combinações fora da distribuição conjunta; mede sensibilidade do classificador nesse ensaio, não efeito causal, erro de previsão ou importância universal.

### Contrafactuais administrativos

Mantive sensores e demais campos, variando somente operador OP-01→OP-07 ou turno 1→3, com reconstrução das features:

| Conjunto | Versão | Intervenção | Mudanças / 4.200 | Taxa % |
|---|---|---|---|---|
| teste | v1 | OP-01_para_OP-07 | 351 | 8,36 |
| teste | v1 | 1_para_3 | 6 | 0,14 |
| teste | v2 | OP-01_para_OP-07 | 462 | 11,00 |
| teste | v2 | 1_para_3 | 17 | 0,40 |
| producao | v1 | OP-01_para_OP-07 | 195 | 4,64 |
| producao | v1 | 1_para_3 | 4 | 0,10 |
| producao | v2 | OP-01_para_OP-07 | 289 | 6,88 |
| producao | v2 | 1_para_3 | 15 | 0,36 |

OP-07 está associado a leituras com maior prevalência: 402/1.008 (39,88%) no teste e 376/990 (37,98%) em produção. A atribuição de operador sênior a equipamentos críticos, descrita no código, é uma explicação de seleção possível. A troca isolada muda decisões mesmo com estado físico preservado, o que exige justificar o uso desse campo. Isso não prova discriminação ou causalidade. Já em F02, demonstrei a dependência direta de alvos futuros, com hipótese distinta.

A normalização de espaços e caixa do identificador preserva decisões e passou. Fonte da associação: [operadores](resultados/associacao_operador.csv). Hipóteses e restrições estão na [metodologia adversarial](docs/metodologia_adversarial.md).

### Casos-limite

Exercitei extremos dentro das faixas declaradas, valores repetidos, lote unitário, tipos não convertíveis, probabilidades nos limites, igualdade ao limiar e ausência/adição de campos. Os defeitos F03–F07 mostram por que executar a inferência sem exceção não é um oráculo suficiente: unidade errada, dropout, posição de campos e impossibilidade física podem produzir saídas numéricas aparentemente normais.

## Qualidade da suíte e reprodução

Na execução em Ubuntu/WSL 2, utilizei uma .venv exclusiva, Python 3.14.4 e versões fixadas em [requirements-lock.txt](requirements-lock.txt). O [README](README.md) apresenta a instalação limpa, o vínculo de dependência ao código original sem escrita nele, variáveis de ambiente e comandos completos ou por etapa.

| Verificação | Resultado observado |
|---|---|
| Exemplos originais | 3 aprovados |
| Suíte externa | 142 casos: 127 aprovados, 15 falhas; 34,59 s |
| Avisos | 1 aviso do parser de datas original com timestamp deliberadamente inválido |
| Ruff | Sem erros |
| mypy | Sem erros em 22 arquivos autorais |
| Cobertura dos auxiliares | 262/264 linhas e ramos: 99,24% |
| Cobertura do Sentinela | 238/245 linhas e ramos: 97,14% |
| Integridade original | 54 arquivos antes/depois; nenhuma divergência |

A cobertura combina oportunidades de linhas e ramos, conforme o JSON. A medida autoral se limita a src/suite_sentinela: não inclui scripts de orquestração nem a própria suíte de testes. Não representa 99,24% de todo o projeto. Defini o limite auxiliar de 95% **após a primeira medição**, considerando o pequeno módulo de cálculo e margem para caminhos de erro; os dois pontos não cobertos são a rejeição de unidade desconhecida. Alta cobertura não substitui a qualidade dos oráculos nem elimina os defeitos demonstrados.

No original, não percorri todos os caminhos defensivos de arquivo ausente/manifesto divergente e validação de ordem de features; não alterei artefatos para aumentar a medida. A cobertura original é informativa, sem impor um limiar de aprovação ao sistema auditado.

Os testes de falhas permanecem asserts normais, sem xfail ou skip. O comando completo termina com **código 1** por essas reprovações; erros de infraestrutura ou análise não são tratados como defeitos esperados. A execução não constitui aprovação de qualidade do Sentinela.

Evidências primárias: [execução estruturada](evidencias/execucao.json), [JUnit](evidencias/pytest.xml), [log pytest](evidencias/pytest.log), [cobertura](evidencias/cobertura.json), [Ruff](evidencias/ruff.log), [mypy](evidencias/mypy.log) e [exemplos](evidencias/exemplos.log). Não realizei execução remota de integração contínua; o comando local pode ser incorporado a esse ambiente.

## Recomendações decorrentes dos resultados

1. Corrigir em trabalho autorizado separado a causalidade das janelas e a origem do risco por motor. Features de uma previsão devem usar somente informações disponíveis naquele instante. Reavaliar ambas as versões em separação temporal após essa correção.
2. Fixar unidade canônica de pressão, revisar imputação de dropout e validar grandezas físicas na entrada. Investigar as violações nos CSVs sem confundir faixa operacional com impossibilidade física.
3. Fazer a inferência por registro validar nomes e ordenar pelos nomes canônicos, rejeitando campos ausentes, inesperados e tipos inválidos.
4. Avaliar v1/v2 pelo compromisso entre recall, precisão e capacidade de manutenção. Os resultados atuais não justificam promoção automática por acurácia; os vazamentos também impedem certificar a v1 como referência segura.
5. Definir custos e critérios operacionais antes de escolher limiar; reservar dados temporais independentes para a decisão e eventual calibração.
6. Monitorar dropout, unidades, caudas, calibração e transições de decisão por motor e período. Investigar a necessidade do operador e a seleção de sua atribuição, sem concluir causalidade a partir de associação.
7. Usar os testes de regressão existentes para verificar futuras correções. Toda recomendação acima permanece proposta: nenhum modelo, dado, limiar ou arquivo do Sentinela foi alterado.

Apresento evidência reproduzível sobre os arquivos fornecidos. Não medi falhas industriais independentes, custo financeiro, latência sob carga ou confiabilidade de uma implantação real; esta avaliação não substitui nova validação após corrigir os defeitos.
