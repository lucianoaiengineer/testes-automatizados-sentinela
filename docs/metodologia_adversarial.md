# Metodologia adversarial e contrafactual

Nos ensaios, utilizei as 4.200 leituras de teste e as 4.200 de produção. Não
forneci o alvo ao pipeline nesses experimentos. v1 e v2 recebem as mesmas
intervenções, com o limiar original de 0,5 e artefatos intactos.

## Ruído de temperatura

Apliquei deslocamentos constantes de −0,4 °C e +0,4 °C somente à temperatura
das leituras. Ambas as magnitudes são estritamente inferiores a ±1 °C da
ficha. Preservei a faixa 45–95 °C por recorte e registrei a magnitude efetiva máxima. O cenário representa um pequeno desvio sistemático do sensor,
não ruído independente a cada hora, e não cobre todos os ruídos possíveis.

Após a intervenção, reconstruí todas as features pelo pipeline
original. Isso mantém as dependências de janelas: uma mudança de leitura pode
atingir várias features. Medi o efeito ponta a ponta, incluindo os defeitos
originais; não atribuí toda mudança somente à floresta isolada.

Registrei número e taxa de decisões alteradas, aberturas e cancelamentos
de alertas, deslocamento médio e máximo da probabilidade. O denominador é o
número de saídas alinhadas. resultados/mudancas_ruido.csv identifica motor,
timestamp e probabilidades de cada mudança. Não existe uma taxa máxima
contratual de instabilidade; os resultados são diagnóstico, não um limite
inventado de aprovação.

## Uma feature por vez

Permutei cada uma das 13 colunas da matriz isoladamente com semente 42.
As outras 12 colunas permanecem idênticas e a distribuição marginal da coluna
alterada é preservada. São 52 combinações de conjunto, versão e feature.
Isso mede dependência funcional do modelo. A quebra de correlações pode criar
combinações fora da distribuição conjunta; a permutação não estima causalidade,
não simula necessariamente um sensor e não deve ser interpretada como redução
de desempenho sem examinar os rótulos.

## Contrafactuais administrativos

Para cada leitura, construí dois cenários, diferentes em exatamente
um campo: id_operador OP-01 versus OP-07, ou turno 1 versus 3. Identidade do
motor, timestamps e todos os sensores permanecem iguais.

Esses campos representam administração/escala de trabalho, não uma alteração
instantânea no estado físico registrado. Entretanto, podem estar associados
a condições reais de operação ou à seleção prévia de motores críticos.
O comentário em features.py informa essa seleção para OP-07. Portanto, neste
experimento investiguei dependência potencialmente problemática, sem concluir
causalidade ilegítima apenas porque a previsão mudou. Frequência de falhas
por operador está em resultados/associacao_operador.csv.

A invariância exigida para mera mudança de caixa/espaços do mesmo operador
é um contrato diferente e possui teste explícito. O teste de alvo futuro é
também separado: manipular falha_72h evidencia acesso direto à resposta,
independentemente da interpretação causal do operador.

## Casos-limite e falhas preservadas

Utilizei fixtures sintéticas válidas para isolar históricos constantes, lotes de um motor,
linha única, extremos operacionais inclusivos, dropout, motor parado,
ausências de campos, valores não convertíveis, NaN/infinito e a igualdade
exata no limiar. Temperatura abaixo do zero absoluto, RMS negativo e idade
negativa testam entradas fisicamente impossíveis. Repetir valores em horários
distintos não equivale a duplicar a chave motor–timestamp.

Os testes de contratos violados permanecem com assert ou pytest.raises que
falha. Não há xfail, skip, repetição até passar ou alteração do Sentinela.
O marcador defeito serve somente à seleção e não modifica o resultado.
Não produzi nem apliquei patch de correção do sistema sob teste.
