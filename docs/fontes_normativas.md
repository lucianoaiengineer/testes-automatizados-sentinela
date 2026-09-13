# Fontes e decisões de escopo

Consulta realizada em 13/09/2026. Os documentos foram lidos diretamente em
`C:/Users/Luciano/Desktop/PUC/2026/TestAutMod`, com acesso ao conteúdo do ZIP
em memória. Nenhum PDF, notebook, imagem de página ou arquivo extraído foi
incluído no projeto. Esta relação registra fontes e decisões, não resultados
de execução da suíte.

## Enunciado formal

`projeto_final_trilha1.pdf`, página única: trabalho de 50 pontos, Trilha 1 de
ML clássico, sobre o Sentinela já treinado, com v1 em produção e v2 candidata.
O documento estabelece os três blocos abaixo, veda alteração do pacote e exige
documentação de pelo menos uma falha real por teste executável que falha.
A entrega precisa conter instruções de reprodução e evidência da suíte rodando.

| Bloco | Requisitos formais | Aplicação planejada |
|---|---|---|
| A — unitários do pipeline | Tipos, faltantes, unidades, faixas, ordem e causalidade temporal. | Testes externos de dados, limpeza e construção das features. |
| B — estatísticos | Comparação v1 × v2 com incerteza; classe rara; limiar; calibração; distribuições teste × produção. | Métricas conjuntas, comparação pareada, curvas por limiar, faixas de calibração e medidas de forma e caudas. |
| C — adversariais | Ruído inferior ao sensor, contrafactuais e casos-limite. | Perturbação de temperatura abaixo de 1 °C, uma feature por vez, campos não físicos e extremos controlados. |

As datas indicadas nas aulas são históricas e divergentes entre si. Para o
planejamento da entrega prevalece o enunciado fornecido, que indica vencimento
em 27 de setembro às 23h59 e disponibilidade até 4 de outubro às 23h59.
Disponibilidade posterior não foi interpretada como prorrogação do vencimento.

## Materiais consultados

Foram consultados seis PDFs, totalizando 138 páginas, e os 14 notebooks
fornecidos. Nos notebooks, foram examinados texto, código e saídas textuais
salvas. Conteúdos idênticos entre versões foram identificados e lidos uma vez;
as diferenças foram examinadas separadamente. O enunciado e as 21 páginas do
PDF da aula 2 não têm camada de texto e foram consultados visualmente.

| Origem | Materiais | Extensão |
|---|---|---|
| Arquivo externo | projeto_final_trilha1.pdf | 1 página |
| aulas.zip / aula1 | Aula 01 - Estratégias de Testes para ML.pdf | 29 páginas |
| aulas.zip / aula1 | Aula 01 - Estratégias de Testes para ML.ipynb; Testes IA - Aula 01.ipynb | 18 células cada |
| aulas.zip / aula2 | aula02.pdf | 21 páginas |
| aulas.zip / aula2 | Aula 02 - TDD e Propriedades.ipynb; Cópia de Aula 02 - TDD e Propriedades.ipynb | 33 e 38 células |
| aulas.zip / aula3 | Aula 3 - Integração em Pipelines e Validação de Dados.pdf | 27 páginas |
| aulas.zip / aula3 | Aula 3 - Integração em Pipelines e Validação de Dados.ipynb; Cópia de Aula 3 - Integração em Pipelines e Validação de Dados.ipynb | 39 células cada |
| aulas.zip / aula4 | Aula04-Testes Estatísticos,AdversarialeFairness.ipynb; Aula04_Testes_Estatísticos,AdversarialeFairness-.ipynb; Aula04_Testes_Estatísticos,AdversarialeFairness.ipynb; Cópia_de_Aula04_Testes_Estatísticos,AdversarialeFairness.ipynb | 23 células cada |
| aulas.zip / aula5 | Aula 05 - Desempenho, Dados Sinteticos e Testes AB (1).pdf | 19 páginas |
| aulas.zip / aula5 | Aula 05 - Desempenho, Dados Sinteticos e Testes AB.ipynb; Aula_05_Desempenho,_Dados_Sinteticos_e_Testes_AB.ipynb; Aula_05_Desempenho,_Dados_Sinteticos_e_Testes_AB_refatorado.ipynb | 31, 31 e 33 células |
| aulas.zip / aula6 | Aula 06 - e2e e Produção.ipynb | 26 células |
| Arquivo externo / aula6 | Aula 06 - e2e e produção.pdf | 41 páginas |

README, guia-do-aluno, configuração, código, exemplos e manifesto do Sentinela
foram consultados na etapa inicial. O guia continua sendo requisito interno,
conforme a solicitação do projeto. A relação bibliográfica da aula 6 é material
de referência: não significa que os artigos nela citados tenham sido fornecidos
ou lidos. O arquivo 00-material-de-consulta.md citado no guia não foi fornecido.

## Aplicação responsável das aulas

| Fonte | Orientação aplicável | Decisão metodológica |
|---|---|---|
| Aula 1, páginas 15–23 | Separar dados, código, modelo e sistema; utilizar fixtures e casos de regressão. | Organizar testes por responsabilidade, com entradas controladas e expectativas fundamentadas. |
| Aula 2, notebook, seções 3–7 | Propriedades só cobrem o domínio declarado; testar faltantes, empates e lotes constantes. | Tratar NaN, infinito, igualdade ao limiar e valores repetidos explicitamente. |
| Aula 2, nota após normalize_batch | Parâmetros derivados do próprio lote alteram a representação na inferência. | Investigar risco por motor e recortes; controlar o histórico necessário às janelas. |
| Aula 3, páginas 11–20 | Validar fronteiras, tipos, completude, faixa e unicidade; limpeza não equivale a validação. | Testar CSVs e saídas intermediárias; usar chave motor–timestamp e contabilizar descartes previstos. |
| Aula 3, práticas 3 e 6 | Conversão deve preservar grandeza física; verificar procedência. | Comparar bar e psi e declarar que os dados publicados são sintéticos. |
| Aula 4, seções 1 e 3 | Comparação pareada e leitura conjunta da matriz de confusão. | Preservar o pareamento v1/v2 e considerar dependência temporal e agrupamento por motor. |
| Aula 4, seção 2 | Robustez a mudanças irrelevantes não significa invariância a qualquer mudança. | Separar invariâncias físicas de exploração de sensibilidade; não impor monotonicidade sem contrato. |
| Aula 5, páginas 5–11 | Examinar caudas e evitar testes que só confirmam uma transformação trivial. | Não transferir limites didáticos de latência; usar amostras controladas apenas para isolar propriedades. |
| Aula 5, páginas 13–17 | Diferença significativa pode favorecer a versão anterior. | Interpretar o sinal do efeito e todos os custos de erro; não promover v2 apenas por acurácia. |
| Aula 6, páginas 3–12 | Oráculos fortes, seleção de testes, isolamento e correção da causa da instabilidade. | Asserts específicos, sementes fixas, marcadores registrados e ausência de repetição até passar. |
| Aula 6, páginas 17–19 | Médias não capturam toda mudança; combinar efeito, incerteza e janela. | Comparar variância, quantis e distribuição; não interpretar p-valor isoladamente como risco operacional. |
| Aula 6, páginas 22–25 | Métrica incorpora escolha sobre erro e custo. | Explicar falsos negativos e positivos sem inventar custos monetários ou recall mínimo. |

Os exemplos de A/B com grupos independentes não serão usados diretamente para
comparar versões que recebem os mesmos registros. A precisão observada não é
necessariamente monotônica na varredura de limiar, embora o conjunto de
positivos previstos diminua com o aumento do limiar. Ausência de significância
também não demonstra equivalência.

Os contrafactuais de operador e turno permitem investigar dependência de
informações administrativas. Não demonstram, isoladamente, causalidade ou
discriminação. A justificativa será vinculada ao código e aos experimentos.

Os exercícios de alteração de implementação, treinamento, implantação e
reversão em produção não autorizam executar essas ações no Sentinela. O material
complementar da outra trilha não acrescenta requisitos ao sistema de ML clássico.
As saídas salvas das aulas não serão apresentadas como resultados deste projeto.

## Próxima etapa

A leitura normativa está concluída para os materiais disponibilizados.
O ambiente Ubuntu em WSL 2 foi confirmado no contexto de usuário correto.
A consulta inicial sob isolamento não enxergava as distribuições desse usuário;
a conclusão preliminar de ausência de Ubuntu foi corrigida. Não houve instalação
de distribuição. Os três exemplos já foram executados com sucesso.
A matriz com funções e resultados acompanha as execuções reais, sem registrar
testes planejados como aprovados.
