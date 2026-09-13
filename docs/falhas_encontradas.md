# Falhas encontradas

Identifiquei os sete grupos abaixo em 15 casos de teste reprovados. Mantive os testes
ativos, com falhas normais. Os comandos pressupõem o ambiente
ativado e configurado conforme o README. Evidência integral: evidencias/pytest.log
e evidencias/pytest.xml. Não apliquei as recomendações ao Sentinela.

## F01 — A média térmica usa leituras futuras

**Hipótese:** uma feature em t depende apenas de leituras até t.
**Teste executável:** tests/test_features.py,
test_leituras_futuras_nao_alteram_feature_passada.
**Evidência e resultado:** mudar somente a temperatura em t=11, de 60 para
90 °C, altera temp_media_6h em t=10 de 60 para 65 °C: diferença de 5 °C no passado.
O teste de recorte com histórico suficiente também falha: 75,106383 no prefixo
contra 75,957447 no lote completo, diferença aproximada de 0,851064 °C.

**Reprodução:** `python -m pytest tests/test_features.py -k 'leituras_futuras or recorte' -v`.
**Causa-raiz:** features.construir aplica rolling(6, center=True), incluindo
observações posteriores na média. O prefixo contém todo o passado da linha
avaliada; portanto, a divergência não se explica por ausência de histórico.
**Impacto operacional:** a representação calculada retrospectivamente difere
da disponível no momento de uma leitura. **Risco para manutenção:** desempenho
offline pode não se reproduzir na antecipação de falhas.
**Recomendação:** projetar janelas causais, verificar equivalência entre lote
e inferência incremental e reavaliar artefatos depois da correção autorizada.

## F02 — O risco do motor depende do alvo do lote

**Hipótese:** alterar somente respostas futuras não altera features passadas.
**Teste executável:** tests/test_features.py,
test_alvo_futuro_nao_altera_risco_passado.
**Evidência e resultado:** alterar de zero para um os 24 últimos alvos de um
lote de 48 registros modifica maquina_risco na primeira linha de 0 para 0,5.
Na linha de base de teste, a acurácia da v1 é 88,5952% com alvo e 76,5238%
sem alvo. Esses números são avaliações distintas, não uma correção do sistema.

**Reprodução:** `python -m pytest tests/test_features.py -k alvo_futuro -v`;
as métricas integrais estão em resultados/linha_base.csv.
**Causa-raiz:** _risco_por_maquina usa a média de falha_72h por motor no lote
quando a coluna existe; sem ela, utiliza risco_maquina.json.
**Impacto operacional:** avaliação rotulada e inferência têm representações
diferentes; há acesso direto à informação que se pretende prever.
**Risco para manutenção:** indicadores retrospectivos podem induzir confiança
incompatível com o uso prospectivo.
**Recomendação:** remover o alvo da construção de features; versionar estatísticas
obtidas somente com informação disponível no corte temporal apropriado e
reavaliar a cadeia completa em separação temporal. Apenas retirar o alvo na
avaliação não corrige a janela centrada nem o treinamento já realizado.

## F03 — Pressões equivalentes chegam em escalas diferentes

**Hipótese:** 3,5 bar e 50,7633 psi representam a mesma pressão para o modelo.
**Teste executável:** tests/test_preprocessamento.py,
test_pressao_equivalente_bar_psi_produz_mesma_feature.
**Evidência e resultado:** as 48 linhas equivalentes entregam feature pressao
igual a 3,5 no primeiro caso e 50,7633 no segundo. Diferença numérica: 47,2633;
razão: 14,5038, o próprio fator de conversão publicado.

**Reprodução:** `python -m pytest tests/test_preprocessamento.py -k pressao_equivalente -v`.
**Causa-raiz:** limpar normaliza o texto de unidade_pressao, mas não converte
o valor; construir transfere pressao numericamente para a matriz, sem unidade.
**Impacto operacional:** a escala recebida depende do CLP de origem.
**Risco para manutenção:** divisões das árvores podem tratar a unidade como
diferença física e deslocar probabilidades ou decisões.
**Recomendação:** adotar unidade canônica, validar a unidade de entrada e testar
equivalência física e idempotência antes de reavaliar os modelos. Neste ensaio,
quantifiquei a divergência da feature, não uma taxa de decisões atribuída só a ela.

## F04 — Dropout de vibração recebe valor fora da faixa

**Hipótese:** uma imputação apresentada como leitura numérica válida respeita
a faixa operacional publicada de 1,2–8 mm/s.
**Teste executável:** tests/test_preprocessamento.py,
test_dropout_nao_se_converte_em_vibracao_fisicamente_invalida.
**Evidência e resultado:** uma ausência é substituída por 0,0 mm/s. Nos CSVs há
1.217 ausências de vibração em treino, 408 em teste e 353 em produção.

**Reprodução:** `python -m pytest tests/test_preprocessamento.py -k dropout -v`.
**Causa-raiz:** VIBRACAO_PADRAO = 0.0 e fillna usam zero sem representação
separada de ausência. As janelas tratam o preenchimento como observação real.
**Impacto operacional:** médias podem diminuir sem redução física da vibração.
**Risco para manutenção:** um sensor sem leitura pode aparentar menor vibração.
**Recomendação:** definir tratamento causal e validado para ausência, com indicador
de disponibilidade e política de inferência; não substituir zero por uma constante
arbitrária apenas para fazer o teste passar. O dropout é permitido na entrada
bruta e não o classifiquei, por si só, como defeito do CSV.

## F05 — Dicionários são interpretados pela ordem, sem validar nomes

**Hipótese:** os mesmos nomes e valores produzem a mesma decisão independentemente
da inserção; uma feature obrigatória não pode ser substituída por chave desconhecida.
**Testes executáveis:** tests/test_modelo.py,
test_registro_independe_da_ordem_de_insercao e test_registro_rejeita_chave_substituida.
**Evidência e resultado:** inverter a ordem de inserção nas primeiras 100 linhas
do teste altera 22 decisões da v1 e 12 da v2. Substituir turno por uma chave
desconhecida mantém 13 valores e não levanta ValueError.

**Reprodução:** `python -m pytest tests/test_modelo.py -k 'ordem_de_insercao or chave_substituida' -v`.
**Causa-raiz:** prever_registro constrói o vetor com registro.values() e valida
somente a quantidade; perde os nomes antes da inferência. A entrada DataFrame,
em contraste, é reorganizada pela ordem canônica e valida campos obrigatórios.
**Impacto operacional:** serialização de um registro pode alterar sua semântica.
**Risco para manutenção:** o painel pode exibir decisões diferentes para o mesmo motor.
**Recomendação:** validar chaves e construir a linha por ordem_features; testar
explicitamente ausências, extras e permutações. Os 22% e 12% referem-se apenas
ao recorte de 100 registros exercitado e não são extrapolados ao conjunto inteiro.

## F06 — Há leituras fora da ficha nos dados publicados

**Hipótese:** valores numéricos observados respeitam as faixas operacionais.
**Teste executável:** tests/test_dados.py, test_faixas_operacionais_dos_dados.
**Evidência e resultado:** treino possui 5 pressões e 4 rotações fora da faixa;
produção possui 1 pressão e 1 rotação. As demais combinações de faixa e conjunto
passaram, inclusive as seis variáveis em teste. Comparei pressão em bar,
sem confundir valores válidos em psi com violações.

**Reprodução:** `python -m pytest tests/test_dados.py -k faixas_operacionais -v`.
**Causa identificada:** os próprios CSVs contêm valores fora do contrato, e o
pipeline não aplica validação completa das faixas. Não pude determinar a causa anterior à publicação
dos CSVs: o simulador não foi disponibilizado.
**Impacto operacional:** a entrada pode violar a ficha sem rejeição explícita.
**Risco para manutenção:** a decisão pode se apoiar em medições fora do domínio
documentado, mesmo com manifesto íntegro.
**Recomendação:** estabelecer validação e política de tratamento na fronteira
de dados; investigar procedência das violações sem editar os dados de avaliação.
Integridade criptográfica confirma a versão, não a correção física.

## F07 — Leituras fisicamente impossíveis recebem decisão

**Hipótese:** entrada fisicamente impossível é rejeitada ou retirada da inferência.
**Teste executável:** tests/test_pipeline.py,
test_leitura_fisicamente_invalida_nao_gera_decisao.
**Evidência e resultado:** cada um dos casos temperatura −274 °C, vibração RMS
−1 mm/s e idade −1 mês produz uma linha de saída, sem rejeição. As probabilidades
observadas são aproximadamente 0,069965, 0,082299 e 0,034624, respectivamente;
as três decisões são zero. Não houve abertura de ordem nesses casos: a falha
é produzir inferência aparentemente válida para uma leitura impossível.

**Reprodução:** `python -m pytest tests/test_pipeline.py -k fisicamente_invalida -v`.
**Causa-raiz:** a limpeza converte alguns tipos e filtra rpm abaixo de 1, mas
não valida esses domínios; o modelo verifica finitude e formato, não significado físico.
**Impacto operacional:** probabilidade numérica não garante validade da entrada.
**Risco para manutenção:** uma decisão negativa pode ocultar falha de aquisição.
**Recomendação:** definir validação física antes da inferência e resposta explícita
de dado inválido. Os extremos válidos da ficha continuam com testes aprovados.
