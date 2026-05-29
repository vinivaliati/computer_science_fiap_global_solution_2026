# Relatório Técnico — Sistema de Monitoramento da Missão GB

**Equipe 35**
**Curso:** Ciência da Computação — FIAP
**Entrega:** Global Solution 2026 — 1º Semestre

---

## 1. Introdução

A Missão GB simula uma estação orbital experimental em órbita baixa terrestre, chamada Estação GB-1. O objetivo do sistema desenvolvido é monitorar continuamente os dados de telemetria da estação, identificar situações de risco, gerar alertas automáticos e recomendar ações corretivas — tudo de forma autônoma, sem depender de intervenção humana imediata.

O cenário é realista: em órbita, a comunicação com a Terra pode ser interrompida, sensores podem falhar e recursos como energia e oxigênio são limitados. O sistema precisa ser capaz de detectar essas situações e agir com base em regras lógicas bem definidas.

O projeto integra os conteúdos das três primeiras fases do curso, aplicando estruturas de dados, lógica booleana, algoritmos e análise de dados em um contexto de operação crítica.

---

## 2. Análise do Problema

### 2.1 Cenário Operacional

A Estação GB-1 opera com seis módulos críticos que não podem falhar simultaneamente sem colocar a missão em risco. São eles: suporte a vida (oxigênio), energia (painéis solares), comunicação com a Terra, habitat (módulo principal), controle de pressão atmosférica e combustível para manobras orbitais.

Além dos módulos, o sistema monitora variáveis ambientais contínuas: geração solar, consumo energético, reserva de bateria, temperatura externa, temperatura interna e nível de radiação ionizante.

### 2.2 Dados Simulados

Os dados foram gerados pelo script `data/dados.py` e cobrem seis meses de operação, de 01/01/2026 a 30/06/2026, com leituras a cada 4 horas — totalizando 1086 registros. Os perfis mensais foram calibrados para simular degradação progressiva ao longo do tempo: a radiação aumenta gradualmente e a reserva de bateria tende a cair nos meses finais, refletindo o desgaste natural dos painéis solares.

Os dados são armazenados em `data/dados.csv` com as seguintes colunas:

```
datetime, geracao_solar_kwh, consumo_kwh, reserva_bateria_pct,
temp_externa_c, temp_interna_c, radiacao_msv,
oxigenio, energia, comunicacao, habitat, pressao, combustivel
```

### 2.3 Inconsistência Proposital

A linha 52 do CSV (08/01/2026 às 08:00) contém uma leitura de geração solar de **980.0 kWh** — valor impossível para uma estação orbital de pequeno porte, cuja capacidade máxima realista fica em torno de 90 kWh no horário de pico. O sistema detecta essa anomalia automaticamente e gera um alerta de inconsistência com recomendação de recalibração do sensor.

### 2.4 Registros Editados Manualmente

Os últimos seis registros do CSV (30/06/2026) foram editados manualmente para simular um cenário de degradação progressiva da bateria ao longo do último dia da missão. O objetivo foi criar uma situação de alerta real para validar o comportamento do sistema de diagnóstico e da previsão de tendência:

| Horário | Bateria |
|---------|---------|
| 00:00 | 58.7% |
| 04:00 | 28.8% |
| 08:00 | 21.4% |
| 12:00 | 17.8% |
| 16:00 | 15.4% |
| 20:00 | 13.0% |

---

## 3. Estruturas de Dados

A escolha das estruturas de dados seguiu o critério de adequação ao tipo de operação realizada sobre cada conjunto de informações.

### 3.1 Listas

Utilizadas para armazenar séries temporais brutas extraídas do CSV: geração solar, consumo, reserva de bateria, radiação e temperatura interna. Listas são a estrutura natural para dados sequenciais — permitem acesso por índice, fatiamento e iteração, que são as operações necessárias para análise de tendência e previsão.

```python
lista_geracao  = [d["geracao_solar_kwh"]  for d in dados]
lista_bateria  = [d["reserva_bateria_pct"] for d in dados]
lista_radiacao = [d["radiacao_msv"]        for d in dados]
```

### 3.2 Fila (FIFO)

Utilizada para organizar os alertas gerados pelas regras lógicas ao longo de todo o período. A fila respeita a ordem cronológica de chegada — o alerta mais antigo é processado primeiro. Isso é importante porque em uma operação real, alertas precisam ser tratados na sequência em que ocorreram para manter rastreabilidade.

A fila é populada ao processar todas as 1086 leituras pelas regras lógicas, não por campos do CSV — garantindo que os eventos reflitam o estado real dos dados.

### 3.3 Pilha (LIFO)

Utilizada para registrar os eventos críticos analisados. A pilha permite acesso imediato ao evento crítico mais recente, que é justamente o mais relevante para a tomada de decisão no momento atual. O topo da pilha sempre contém o último crítico detectado.

### 3.4 Dicionário

Utilizado para armazenar o estado atual de cada módulo com acesso direto pelo nome. Cada entrada contém: nome legível, descrição funcional, status booleano atual e total histórico de falhas. O acesso por chave (O(1)) é mais eficiente do que percorrer uma lista quando se quer consultar um módulo específico.

```python
modulos = {
    "oxigenio": {
        "nome":         "Suporte a Vida - Oxigenio",
        "descricao":    "Fornecimento e monitoramento de oxigenio respiravel",
        "status":       bool(dados[-1]["oxigenio"]),
        "total_falhas": sum(1 for d in dados if not d["oxigenio"]),
    },
    ...
}
```

### 3.5 Hierarquia (Dicionário Aninhado)

Utilizada para representar a estrutura organizacional da missão, dividida em dois subsistemas principais: energia e habitat. Essa estrutura reflete como os sistemas da estação se relacionam hierarquicamente e facilita a visualização do estado geral da missão de forma estruturada.

```python
hierarquia = {
    "missao_gb": {
        "energia":  { "geracao_solar": ..., "reserva_bateria": ... },
        "habitat":  { "oxigenio": ..., "temperatura_interna": ..., "pressao": ... }
    }
}
```

### 3.6 Matriz (Lista de Listas)

Utilizada para representar as leituras das últimas 24 horas organizadas por horário e variável. Cada linha da matriz corresponde a um horário (00:00, 04:00, ..., 20:00) e cada coluna a uma variável (geração solar, consumo, bateria, temperatura interna, radiação). Essa estrutura facilita a visualização tabular do estado recente da estação.

---

## 4. Regras Lógicas

### 4.1 Limiares de Classificação

As variáveis contínuas são classificadas em três faixas de operação:

| Variável | Normal | Alerta | Crítico |
|----------|--------|--------|---------|
| Bateria | ≥ 25% | 15–24% | < 15% |
| Radiação | ≤ 0.6 mSv/h | 0.6–1.0 mSv/h | > 1.0 mSv/h |
| Temp. interna | 10–30°C | 5–10°C ou 30–35°C | < 5°C ou > 35°C |
| Geração solar | — | > 200 kWh | — |

Os módulos críticos usam status booleano: `True` indica funcionamento normal, `False` indica falha. Qualquer módulo em `False` eleva o diagnóstico imediatamente para CRÍTICO, sem possibilidade de compensação por outras variáveis normais — o raciocínio é que módulos como oxigênio e pressão não admitem degradação parcial.

### 4.2 Expressão Booleana Principal

```
CRITICO = (NOT oxigenio OR NOT energia OR NOT comunicacao
           OR NOT habitat OR NOT pressao OR NOT combustivel)
       OR (count_alertas >= 2)
       OR (radiacao > 1.0 AND NOT comunicacao)
```

### 4.3 Regras com Operadores Lógicos

**Regra 1 — Falha de módulo (OR, NOT):**
Qualquer módulo com `status = False` eleva o diagnóstico para CRÍTICO imediatamente. Um único ponto de falha em sistemas vitais é suficiente para comprometer a missão.

```python
for nome, mod in modulos.items():
    if not mod["status"]:
        criticos.append(f"falha_{nome}")
```

**Regra 2 — Múltiplos alertas simultâneos (AND implícito na contagem):**
Se duas ou mais variáveis estiverem em estado de alerta ao mesmo tempo, o diagnóstico é elevado para CRÍTICO. A lógica aqui é que a combinação de múltiplos problemas simultâneos representa um risco maior do que cada um isoladamente.

```python
if len(alertas) >= 2:
    criticos.append("multiplos_alertas")
```

**Regra 3 — Radiação crítica sem comunicação (AND, NOT):**
Se a radiação está acima de 1.0 mSv/h e a comunicação com a Terra está perdida ao mesmo tempo, o sistema gera um crítico adicional. Sem comunicação, não é possível solicitar apoio externo durante uma situação de radiação elevada.

```python
if leitura["radiacao_msv"] > 1.0 and not modulos["comunicacao"]["status"]:
    criticos.append("radiacao_critica")
```

### 4.4 Estrutura de Decisão

O sistema usa IF/ELIF/ELSE para classificar o estado final:

```python
if criticos:
    return "CRITICO", alertas, criticos
elif alertas:
    return "ALERTA", alertas, criticos
else:
    return "NORMAL", alertas, criticos
```

---

## 5. Alertas e Recomendações

### 5.1 Geração de Alertas

Os alertas são gerados em tempo real ao processar cada leitura pelas regras lógicas. Cada alerta é classificado em ALERTA ou CRÍTICO e inclui o motivo e o modo operacional ativado automaticamente em resposta:

```
[ALERTA] 2026-06-30 08:00 - Bateria baixa -> modo economia ativado
[CRÍTICO] 2026-05-30 12:00 - Falha no oxigenio -> reserva de oxigenio ativada
```

### 5.2 Recomendações Automáticas

As recomendações são geradas a partir de um dicionário que mapeia cada causa para uma ação específica. Os críticos são sempre exibidos antes dos alertas:

| Causa | Nível | Recomendação |
|-------|-------|--------------|
| Bateria baixa (< 25%) | ALERTA | Reduzir consumo não essencial e priorizar recarga |
| Bateria crítica (< 15%) | CRÍTICO | Desligar sistemas não essenciais imediatamente |
| Radiação elevada (> 0.6) | ALERTA | Acionar blindagem e reduzir exposição da tripulação |
| Radiação crítica (> 1.0) | CRÍTICO | Evacuar módulos expostos e acionar protocolo de emergência |
| Falha no oxigênio | CRÍTICO | Ativar reserva de oxigênio de emergência |
| Falha na comunicação | CRÍTICO | Ativar rádio de emergência de baixa frequência |
| Múltiplos alertas (2+) | CRÍTICO | Acionar protocolo de crise geral da missão |

---

## 6. Análise e Previsão de Dados

### 6.1 Variável Analisada

A variável escolhida para previsão foi a **reserva de bateria** (`reserva_bateria_pct`), por ser a variável com tendência de queda mais clara ao longo do tempo e com maior impacto direto na operação da estação. Uma bateria em nível crítico compromete todos os sistemas simultaneamente.

### 6.2 Metodologia

O sistema aplica dois métodos em sequência, ambos implementados manualmente sem bibliotecas externas:

**Passo 1 — Média Móvel (janela = 6 leituras / 24h):**

A bateria oscila naturalmente com o ciclo solar — carrega durante o dia e descarrega à noite. Aplicar regressão linear diretamente sobre esses dados brutos gera um coeficiente próximo de zero, pois as oscilações se cancelam. A média móvel suaviza esse ruído e revela a tendência real de consumo.

```python
def media_movel(valores, janela=6):
    suavizado = []
    for i in range(len(valores)):
        inicio = max(0, i - janela + 1)
        suavizado.append(sum(valores[inicio:i+1]) / (i - inicio + 1))
    return suavizado
```

**Passo 2 — Regressão Linear por Mínimos Quadrados:**

Aplicada sobre a série suavizada. Os coeficientes `a` (inclinação) e `b` (intercepto) são calculados pelas fórmulas dos mínimos quadrados:

```
a = (n × Σxy − Σx × Σy) / (n × Σx² − (Σx)²)
b = (Σy − a × Σx) / n
```

A equação resultante `y = ax + b` é usada para projetar os próximos 12 valores (48 horas).

### 6.3 Base e Horizonte

- **Base de cálculo:** últimas 42 leituras (7 dias)
- **Horizonte de previsão:** próximas 12 leituras (48 horas)

### 6.4 Resultado e Influência na Decisão

Com os dados editados manualmente no último dia, a regressão capturou a tendência de queda e gerou um coeficiente negativo (`a = -0.2170`), indicando declínio progressivo. A previsão projeta a bateria saindo de ~41% e chegando a ~39% em 48 horas.

Quando a previsão indica que a bateria vai atingir o limiar de alerta (< 25%) ou crítico (< 15%) dentro das próximas 48 horas, o sistema dispara automaticamente um aviso antecipado com a recomendação correspondente — permitindo ação preventiva antes que a situação se torne crítica.

---

## 7. Decisões Técnicas

**Por que CSV e não JSON?**
CSV é mais simples de editar manualmente e mais legível para dados tabulares com muitas linhas. Como os dados têm estrutura regular (mesmas colunas em todas as linhas), CSV é a escolha mais adequada.

**Por que a fila é populada pelas regras lógicas e não pelo CSV?**
Inicialmente os eventos eram armazenados como colunas no CSV. Porém, isso criava uma separação entre os dados brutos e o diagnóstico — um evento no CSV poderia ser classificado de forma diferente das regras do sistema. Centralizar a geração de alertas nas regras lógicas garante consistência: o que aparece na fila é exatamente o que o sistema diagnosticou.

**Por que média móvel antes da regressão?**
A bateria oscila com o ciclo solar — sobe de dia e cai à noite. Sem suavização, a regressão linear sobre dados brutos encontra uma tendência quase plana, pois as oscilações se cancelam. A média móvel com janela de 24 horas elimina esse ruído e permite que a regressão capture a tendência real de longo prazo.

**Por que 7 dias de base para a previsão?**
Um período muito curto (1-2 dias) captura apenas as oscilações recentes e é sensível a eventos pontuais. Um período muito longo dilui o impacto de mudanças recentes. Sete dias representa um equilíbrio — suficiente para capturar a tendência sem ser dominado por dados antigos.

**Por que os módulos usam boolean e não inteiro?**
O enunciado pede explicitamente variáveis booleanas para indicar o funcionamento de módulos críticos. Além disso, boolean é semanticamente mais preciso: um módulo não está "50% funcionando" — ou funciona ou não funciona.

---

## 8. Conclusões

O sistema de monitoramento da Missão GB atingiu todos os objetivos propostos: lê e interpreta dados de telemetria, organiza as informações em estruturas adequadas, aplica regras lógicas para classificar situações operacionais, gera alertas automáticos com recomendações específicas e prevê o comportamento da bateria nas próximas 48 horas.

A principal dificuldade do projeto foi calibrar os dados simulados para que fossem realistas e ao mesmo tempo gerassem situações de alerta em frequência adequada — nem raras demais para não testar o sistema, nem tão frequentes que tornassem o diagnóstico trivial. Isso exigiu várias iterações de ajuste nos perfis mensais e nos limiares das regras.

A combinação de média móvel com regressão linear mostrou-se mais eficaz do que a regressão direta sobre dados brutos, pois elimina o ruído do ciclo solar e revela a tendência real de consumo ao longo do tempo.

Do ponto de vista técnico, o projeto reforçou a importância de escolher estruturas de dados adequadas para cada operação: listas para séries temporais, fila para rastreabilidade cronológica de alertas, pilha para acesso imediato ao evento mais recente e dicionário para consulta eficiente por nome de módulo.

---

## 9. Exemplo de Execução Real

Abaixo está a saída completa do sistema executado com os dados da Missão GB, incluindo os registros manuais do último dia:

```
Leituras carregadas: 1086

--- MODULOS ---
  Suporte a Vida - Oxigenio: OK | Falhas historicas: 7
  Energia - Paineis Solares: OK | Falhas historicas: 4
  Comunicacao - Link Terra: OK | Falhas historicas: 6
  Habitat - Modulo Principal: OK | Falhas historicas: 7
  Pressao - Atmosfera Interna: OK | Falhas historicas: 5
  Combustivel - Propulsao: OK | Falhas historicas: 4

--- ULTIMOS 10 EVENTOS EM ALERTA/CRITICO ---
  [CRITICO] 2026-05-16 16:00 - Falha no habitat -> protocolo de integridade estrutural ativado
  [CRITICO] 2026-05-26 00:00 - Falha no oxigenio -> reserva de oxigenio ativada
  [CRITICO] 2026-05-28 08:00 - Falha na pressao -> despressurizacao controlada iniciada
  [CRITICO] 2026-05-30 12:00 - Falha no oxigenio -> reserva de oxigenio ativada
  [CRITICO] 2026-06-02 04:00 - Falha no oxigenio -> reserva de oxigenio ativada
  [CRITICO] 2026-06-08 20:00 - Falha na comunicacao -> radio de emergencia ativado
  [ALERTA]  2026-06-30 08:00 - Bateria baixa -> modo economia ativado
  [ALERTA]  2026-06-30 12:00 - Bateria baixa -> modo economia ativado
  [ALERTA]  2026-06-30 16:00 - Bateria baixa -> modo economia ativado
  [ALERTA]  2026-06-30 20:00 - Bateria baixa -> modo economia ativado

--- PILHA DE CRITICOS (topo = mais recente) ---
  2026-05-30 12:00 - Falha no oxigenio
  2026-06-02 04:00 - Falha no oxigenio
  2026-06-08 20:00 - Falha na comunicacao

--- DIAGNOSTICO ATUAL (2026-06-30 20:00) ---
  Status: ALERTA
  [ALERTA]  Bateria baixa

--- RECOMENDACOES ---
  1. [ALERTA] Bateria baixa: Reduzir consumo nao essencial e priorizar recarga

--- PREVISAO DE BATERIA (proximos 2 dias / 12 leituras) ---
  Metodo: media movel (janela=6) + regressao linear
  Regressao linear: y = -0.2170x + 50.5401
  Base: ultimas 42 leituras (7 dias)
  +  4h:  41.4%
  +  8h:  41.2%
  + 12h:  41.0%
  + 16h:  40.8%
  + 20h:  40.6%
  + 24h:  40.3%
  + 28h:  40.1%
  + 32h:  39.9%
  + 36h:  39.7%
  + 40h:  39.5%
  + 44h:  39.3%
  + 48h:  39.0%
  Bateria prevista dentro dos limites normais nas proximas 48h

--- MATRIZ 24H ---
  datetime              solar  consumo  bateria   t_int     rad
  2026-06-30 00:00       0.76    50.46     58.7    24.3   0.639
  2026-06-30 04:00       3.21    47.92     28.8    24.7   0.429
  2026-06-30 08:00      12.02    56.86     21.4    20.5   0.343
  2026-06-30 12:00      35.39    55.31     17.8    23.9   0.470
  2026-06-30 16:00      15.54    47.36     15.4    20.5   0.464
  2026-06-30 20:00       1.01    52.15     15.2    20.8   0.298
```

### Interpretação da Saída

O diagnóstico final é **ALERTA** por bateria baixa (15.2%), próxima do limiar crítico de 15%. Os últimos 10 eventos mostram uma concentração de falhas críticas em maio e junho — oxigênio, pressão e comunicação — seguidas pela degradação progressiva da bateria no último dia, resultado dos registros editados manualmente para simular o cenário.

A pilha de críticos confirma que os três eventos mais recentes foram falhas de oxigênio e comunicação, evidenciando o padrão de deterioração da estação ao longo dos seis meses.

A previsão indica que, mantendo o ritmo atual de consumo, a bateria deve cair de ~41% para ~39% nas próximas 48 horas — dentro dos limites normais, mas com tendência negativa que justifica a recomendação de redução de consumo já emitida pelo sistema.