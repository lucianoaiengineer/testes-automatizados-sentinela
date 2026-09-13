# Metodologia estatística

## População e unidade de análise

Os CSVs publicados pelo Sentinela são dados sintéticos do simulador descrito
no README. São os dados efetivos do sistema sob teste, não observações de uma
empresa real. Treino tem 16.800 registros; teste e produção têm 4.200 cada.
Os períodos são consecutivos, com 25 motores e leituras horárias.

O alvo indica falha nas próximas 72 horas. Leituras próximas compartilham
histórico e horizonte do alvo; 4.200 linhas não são 4.200 eventos independentes.
As contagens de falsos negativos e positivos são de leituras classificadas,
não de motores queimados ou ordens distintas de manutenção. Não existe no
contrato uma política de consolidação de alertas em ordens únicas.

## Dois modos de avaliação

1. **Rotulado:** reproduzi a chamada sugerida no README, fornecendo falha_72h
   ao pipeline e medindo suas saídas sem modificar o sistema.
2. **Sem alvo:** retirei apenas falha_72h da entrada e mantive os rótulos numa
   estrutura externa para avaliar as mesmas linhas. Esse cenário se aproxima
   da informação disponível na inferência.

Os dois cenários ainda usam a construção original de janelas. Retirar o alvo
não remove o uso de temperaturas futuras pela janela centrada nem desfaz
problemas incorporados durante o treinamento. Assim, nem o cenário sem alvo
é uma estimativa livre de todo vazamento temporal.

Utilizei treino como diagnóstico de ajuste e referência, não como estimativa de
generalização. Não usei teste e produção para treinar, recalibrar ou
escolher configurações que fossem aplicadas ao sistema.

## Métricas e comparação

A matriz usa positivo = falha: VP, VN, FP e FN. Acurácia é (VP+VN)/N,
precisão é VP/(VP+FP), recall é VP/(VP+FN) e F1 é 2VP/(2VP+FP+FN).
Denominadores nulos produzem zero, seguindo a convenção do painel.
A prevalência é (VP+FN)/N. O classificador trivial sempre prevê zero;
sua acurácia é 1 menos a prevalência e seu recall é zero.

O recall responde quantas leituras associadas a falha foram identificadas;
a precisão ajuda a estimar o volume de alertas sem falha observada. Não atribuí
custos monetários, recall mínimo ou equivalência entre FP e FN sem fundamento.

Utilizei bootstrap pareado e agrupado por motor: em cada uma das 2.000 repetições,
sorteiam-se 25 motores com reposição. Cada motor leva sua série completa,
os mesmos rótulos e as previsões das duas versões. Somam-se as contagens e
recalculam-se as quatro métricas. O efeito é sempre v2 menos v1; o intervalo
percentil de 95% usa quantis 2,5% e 97,5%. Semente: 42.

Preservar séries evita tratar leituras horárias como independentes, mas pressupõe
independência aproximada entre motores. Choques comuns à planta, poucos grupos,
seleção dos motores e apenas uma semana por avaliação limitam a inferência.
As previsões ficam fixas no bootstrap: mede-se incerteza da avaliação, não do
treinamento. Intervalos por métrica são marginais; não constituem uma garantia
simultânea sobre todas as métricas. Não escolhi intervalos após testar
sementes em busca de significância. Intervalo que inclui zero é inconclusivo,
não prova igualdade ou equivalência.

## Limiar e calibração

A varredura fixa vai de 0 a 1, inclusive, em passos de 0,01, totalizando 101
limiares. Decisão positiva usa probabilidade maior ou igual ao limiar. Positivos
previstos e recall não aumentam quando o limiar sobe; a precisão empírica pode
oscilar. A varredura é exploratória: escolher um novo limiar exigiria uma
partição temporal de validação, custos e restrições operacionais definidos
antes da avaliação final.

Na calibração, utilizei dez faixas de mesma largura em [0,1]. O valor 1 entra na
última faixa. Registrei quantidade, probabilidade média e frequência
observada; faixas vazias permanecem sem estimativa. Brier é a média de
(probabilidade−alvo)². ECE é a média ponderada das diferenças absolutas entre
probabilidade e frequência por faixa. ECE depende da discretização e do
tamanho amostral. Não criei um limite de aprovação sem contrato.

## Distribuições

Comparei teste e produção nas seis variáveis da ficha com faixas
numéricas, mais horas_operacao e turno. Converti pressão para bar somente
na auditoria; essa conversão não modifica a entrada dos testes do pipeline.
Excluí dropouts de vibração apenas dos cálculos da distribuição dessa
variável e suas contagens permanecem visíveis no inventário. Oito comparações
incluem médias, variâncias amostrais, quantis 1/5/50/95/99, caudas fora de
p01–p99 de teste, diferença de médias padronizada e distância de Wasserstein.

KS fornece uma distância entre distribuições empíricas. Seu p-valor nominal,
que salvei com sufixo iid_exploratorio, pressupõe independência das linhas; não o
utilizei como prova confirmatória com essas séries. Para turno, que é discreto,
essa ressalva é ainda mais importante. A comparação principal de incerteza
troca os períodos inteiros dentro de cada motor, com 1.999 permutações e
semente 42. Usa o máximo da diferença absoluta entre médias das funções de
distribuição por motor, sobre 201 quantis comuns, com peso igual para motores.
O p-valor é (1 + permutações tão extremas)/(1 + número de permutações).

Holm ajusta os oito p-valores por multiplicidade. A permutação depende da
permutabilidade dos períodos sob a hipótese nula; envelhecimento, tendências
e mudanças compartilhadas entre motores podem violá-la. A grade aproxima a
distância e pode perder mudanças localizadas. Baixa potência com 25 grupos
impede interpretar um resultado não significativo como estabilidade.
Tabulei as frequências das categorias de operador, motor, unidade e alvo.
Inspecionar entradas não basta para demonstrar ou excluir drift conceitual.

## Reprodutibilidade e limites numéricos

Resultados integrais estão em resultados/ e os comandos no README. Sementes,
quantidade de repetições, faixas e grades são fixos. Contagens e decisões usam
igualdade exata; comparações de ponto flutuante usam aproximação, em geral
1e-12 para reprodução numérica. O teste de equivalência bar/psi admite erro
numérico muito menor que a discrepância física investigada. Os limites de
aprovação física vêm da ficha de sensores, não dos valores observados.
