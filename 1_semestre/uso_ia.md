# Uso de Inteligência Artificial — Missão GB

## Como a IA foi utilizada

### Geração e ajuste dos dados simulados

A IA foi usada para auxiliar na geração do script `data/dados.py`, que cria o arquivo `dados.csv` com 1086 leituras de telemetria. A equipe definiu os parâmetros do cenário (período, módulos, variáveis, limiares), e a IA ajudou a estruturar o código de geração. Os valores dos perfis mensais e a inconsistência proposital foram discutidos e ajustados iterativamente pela equipe até refletir um comportamento realista de degradação ao longo de seis meses.

Os últimos seis registros do CSV foram editados manualmente pela equipe para simular um cenário específico de queda progressiva de bateria.

### Revisão e explicação de conceitos

Durante o desenvolvimento, a IA foi consultada para esclarecer dúvidas sobre estruturas de dados (diferença prática entre fila FIFO e pilha LIFO), sobre a formulação matemática da regressão linear por mínimos quadrados e sobre como a média móvel suaviza séries temporais com ruído cíclico.

### Auxílio na escrita do relatório e README

A IA auxiliou na estruturação e redação do relatório técnico e do README. Os textos foram revisados e adaptados pela equipe para refletir as decisões reais tomadas ao longo do projeto, incluindo ajustes de tom, remoção de trechos genéricos e adição de detalhes específicos do nosso cenário.

---

## Validação crítica

Tudo que a IA produziu foi revisado e adaptado pela equipe antes de ser incorporado ao projeto. Os principais pontos de validação foram:

- Os dados simulados foram analisados para garantir que os limiares de alerta e crítico fossem atingidos com frequência adequada — nem raramente demais (o que não testaria o sistema) nem com tanta frequência que tornasse o diagnóstico trivial. Isso exigiu múltiplas iterações de ajuste nos perfis mensais.
- As regras lógicas foram discutidas pela equipe e os limiares foram definidos com base no que fazia sentido para o cenário operacional escolhido, não apenas nos valores sugeridos inicialmente.
- O relatório e o README foram revisados para garantir que as explicações refletissem o entendimento real da equipe sobre as escolhas técnicas feitas.

---

## O que não foi gerado por IA

- A definição do cenário (Estação GB-1, módulos escolhidos, período da missão)
- Os limiares finais de alerta e crítico para cada variável
- A decisão de combinar média móvel com regressão linear
- A edição manual dos registros do último dia para criar o cenário de degradação de bateria
- A validação do comportamento do sistema rodando localmente