# Missão GB — Sistema Inteligente de Monitoramento Orbital

Simulação de um sistema de monitoramento operacional para a Estação GB-1, uma estação orbital experimental em órbita baixa terrestre. O sistema interpreta dados de telemetria, classifica situações críticas, gera alertas automáticos e prevê o comportamento da reserva de bateria usando regressão linear com média móvel.

---

## Equipe 35

| Nome | RM |
|------|----|
| Arthur Apolonio de Oliveira | rm571385
| Matheus Bejarano da Costa Resende | rm569195
| Dayvid Daniel Duarte Ramos | rm569482
| Bryan Lima Garcia | rm573611
| Vinicius Valiati Costa | rm568674

---

## Organização do Repositório

```
missao_gb/
├── src/
│   └── sistema.py       # sistema principal de monitoramento
├── data/
│   ├── dados.py         # gerador do arquivo de telemetria
│   └── dados.csv        # dados simulados da missão (Jan–Jun 2026)
├── docs/
│   ├── relatorio.pdf    # relatório técnico
│   ├── link_video.txt   # link do vídeo de apresentação
│   └── uso_ia.md        # registro do uso de IA
└── README.md
```

---

## Resumo do Problema

A Estação GB-1 depende do monitoramento contínuo para garantir a segurança da tripulação e a integridade dos equipamentos. Em ambientes onde a comunicação pode ser intermitente, o sistema precisa ser capaz de interpretar dados de sensores em tempo real, identificar anomalias, gerar alertas automáticos e recomendar ações corretivas sem intervenção humana imediata.

O sistema processa 1086 leituras de telemetria coletadas de janeiro a junho de 2026, em intervalos de 4 horas, cobrindo 6 módulos críticos e variáveis ambientais como temperatura, radiação e reserva de bateria.

---

## Dados Simulados

Os dados foram gerados pelo script `data/dados.py` e cobrem o período de **01/01/2026 a 30/06/2026**, com leituras a cada 4 horas (1086 registros no total).

### Módulos Críticos (status binário: 1 = OK, 0 = FALHA)

| Módulo | Descrição |
|--------|-----------|
| `oxigenio` | Fornecimento e monitoramento de oxigênio respirável |
| `energia` | Geração de energia via painéis solares fotovoltaicos |
| `comunicacao` | Canal de comunicação bidirecional com a Terra |
| `habitat` | Integridade estrutural e conforto da tripulação |
| `pressao` | Controle da pressão atmosférica interna |
| `combustivel` | Reserva de combustível para manobras orbitais |

### Variáveis de Telemetria

| Variável | Unidade | Descrição |
|----------|---------|-----------|
| `geracao_solar_kwh` | kWh | Energia gerada pelos painéis solares |
| `consumo_kwh` | kWh | Consumo energético da estação |
| `reserva_bateria_pct` | % | Carga atual das baterias |
| `temp_externa_c` | °C | Temperatura externa da estação |
| `temp_interna_c` | °C | Temperatura interna do habitat |
| `radiacao_msv` | mSv/h | Nível de radiação ionizante |

### Inconsistência Proposital

A linha 52 do CSV (08/01/2026 às 08:00) contém uma leitura de geração solar de **980.0 kWh**, valor impossível para uma estação orbital de pequeno porte. O sistema detecta essa anomalia e gera um alerta de inconsistência com recomendação de recalibração do sensor.

### Registros Manuais

Os últimos 6 registros do CSV (30/06/2026) foram editados manualmente para simular um cenário de degradação progressiva da bateria ao longo do dia, permitindo validar o diagnóstico de alerta e a previsão de tendência de queda do sistema:

```
2026-06-30 00:00 → bateria: 58.7%
2026-06-30 04:00 → bateria: 28.8%
2026-06-30 08:00 → bateria: 21.4%
2026-06-30 12:00 → bateria: 17.8%
2026-06-30 16:00 → bateria: 15.4%
2026-06-30 20:00 → bateria: 13.0%  ← diagnóstico atual
```

---

## Estruturas de Dados

| Estrutura | Uso |
|-----------|-----|
| **Lista** | Séries temporais de geração solar, consumo, bateria, radiação e temperatura interna |
| **Fila** | Alertas pendentes organizados por ordem de ocorrência o mais antigo é processado primeiro |
| **Pilha** | Eventos críticos analisados o topo sempre contém o evento crítico mais recente |
| **Dicionário** | Estado atual de cada módulo, com nome, descrição, status booleano e total de falhas históricas |
| **Hierarquia** | Estrutura aninhada representando a organização da missão em subsistemas de energia e habitat |
| **Matriz (lista de listas)** | Leituras das últimas 24h organizadas por horário × variável |

---

## Regras Lógicas Principais

### Limiares de Classificação

| Variável | Normal | Alerta | Crítico |
|----------|--------|--------|---------|
| Bateria | ≥ 25% | 15–24% | < 15% |
| Radiação | ≤ 0.6 mSv/h | 0.8–1.0 | > 1.0 mSv/h |
| Temp. interna | 10–30°C | 5–10 ou 30–35°C | < 5°C ou > 35°C |
| Geração solar | — | > 200 kWh (inconsistência) | — |

### Expressão Booleana Principal

```
CRITICO = (NOT oxigenio OR NOT energia OR NOT comunicacao
           OR NOT habitat OR NOT pressao OR NOT combustivel)
       OR (count_alertas >= 2)
```

### Regras com Operadores Lógicos

1. Qualquer módulo com `status = False` → **CRÍTICO** imediato
2. `len(alertas) >= 2` → **CRÍTICO** por múltiplos alertas simultâneos

---

## Técnica de Previsão

**Variável analisada:** Reserva de bateria (`reserva_bateria_pct`)

**Método:** Média móvel (janela = 6 leituras / 24h) seguida de regressão linear por mínimos quadrados, ambas implementadas manualmente sem bibliotecas externas.

**Base:** Últimas 42 leituras (7 dias)  
**Horizonte:** Próximas 12 leituras (48h)

**Fórmula da regressão:**
```
y = a × x + b
```
Onde os coeficientes são calculados por:
```
a = (n × Σxy − Σx × Σy) / (n × Σx² − (Σx)²)
b = (Σy − a × Σx) / n
```

A média móvel suaviza as oscilações do ciclo solar antes da regressão, tornando a tendência mais representativa. Se a previsão indicar bateria abaixo de 25% ou 15% nas próximas 48h, o sistema dispara aviso e recomendação automática.

---

## Como Executar

1. Clone o repositório:
```
git clone https://github.com/vinivaliati/computer_science_fiap_global_solution_2026/blob/main/1_semestre
cd missao-gb
```

2. Gere o arquivo de dados (executar na pasta `data/`):
```
cd data
python dados.py
```
Isso cria o `dados.csv` na mesma pasta. Porem caso queiram ja subimos o nosso csv, ja que tem apenas 1086 linhas.

3. Execute o sistema (executar na pasta raiz):
```
python src/sistema.py
```

**Requisitos:** Python 3.x, apenas bibliotecas padrão (`csv`, `os`)

---

## Exemplo de Entrada e Saída

**Entrada (última leitura do CSV):**
```
datetime: 2026-06-30 20:00
geracao_solar_kwh: 1.01
consumo_kwh: 52.15
reserva_bateria_pct: 13.0
temp_interna_c: 20.8
radiacao_msv: 0.298
todos os módulos: OK
```

**Saída:**
```
--- DIAGNOSTICO ATUAL (2026-06-30 20:00) ---
  Status: ALERTA
  [ALERTA] Bateria baixa

--- RECOMENDACOES ---
  1. [ALERTA] Bateria baixa: Reduzir consumo nao essencial e priorizar recarga

--- PREVISAO DE BATERIA (proximos 2 dias / 12 leituras) ---
  Metodo: media movel (janela=6) + regressao linear
  Regressao linear: y = -0.2170x + 50.5401
  Base: ultimas 42 leituras (7 dias)
  +  4h:  41.4%
  + 48h:  39.0%
  Bateria prevista dentro dos limites normais nas proximas 48h
```

---

## Recomendações Automáticas

| Causa | Nível | Recomendação |
|-------|-------|--------------|
| Bateria baixa (< 25%) | ALERTA | Reduzir consumo não essencial e priorizar recarga |
| Bateria crítica (< 15%) | CRÍTICO | Desligar sistemas não essenciais imediatamente |
| Radiação elevada (> 0.6) | ALERTA | Acionar blindagem e reduzir exposição da tripulação |
| Radiação crítica (> 1.0) | CRÍTICO | Evacuar módulos expostos e acionar protocolo de emergência |
| Temperatura em alerta | ALERTA | Verificar sistema de climatização |
| Temperatura crítica | CRÍTICO | Acionar sistema de emergência térmico imediatamente |
| Falha no oxigênio | CRÍTICO | Ativar reserva de oxigênio de emergência |
| Falha na energia | CRÍTICO | Alternar para baterias de reserva |
| Falha na comunicação | CRÍTICO | Ativar rádio de emergência de baixa frequência |
| Falha no habitat | CRÍTICO | Verificar integridade estrutural e pressurização |
| Falha na pressão | CRÍTICO | Acionar protocolo de despressurização controlada |
| Falha no combustível | CRÍTICO | Suspender manobras orbitais imediatamente |
| Inconsistência solar | ALERTA | Recalibrar sensor de geração solar |
| Múltiplos alertas (2+) | CRÍTICO | Acionar protocolo de crise geral da missão |

---

## Link do Vídeo

[[link do vídeo no YouTube](https://youtu.be/Su2JB2KjFdw)]

---

## Conclusões e Aprendizados

O desenvolvimento do sistema de monitoramento da Missão GB permitiu aplicar de forma integrada os conceitos das três primeiras fases do curso: estruturas de dados, lógica booleana, algoritmos de busca e análise de dados.

A principal dificuldade foi calibrar os dados simulados para que fossem realistas e ao mesmo tempo gerassem situações de alerta em uma frequência adequada, nem raras demais para não testar o sistema, nem frequentes demais para não trivializar o diagnóstico.

Apesar de ser permitido o uso de bibliotecas externas, optamos por desenvolver a solução utilizando o máximo possível de Python "puro", com o objetivo de reforçar e consolidar nossos conhecimentos na linguagem.