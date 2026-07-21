# Funcionamento atual do Content Radar

Este documento descreve o funcionamento atual do sistema, incluindo o fluxo de coleta, análise, persistência e envio de mensagens para o Telegram, além de como esse processo deveria ser orquestrado em etapas quando o projeto for executado na nuvem.

## 1. Visão geral do sistema

O Content Radar é uma aplicação em Python que reúne sinais de conteúdo de diferentes fontes para identificar temas relevantes no mercado editorial e literário. O objetivo é transformar esses sinais em insights úteis para conteúdo curto, especialmente para plataformas como YouTube, TikTok e Instagram Reels.

O sistema funciona em quatro etapas principais:

1. Coleta de sinais
2. Persistência no banco de dados
3. Análise com Gemini
4. Entrega do resumo via Telegram

---

## 2. Arquitetura geral

A aplicação está organizada em camadas:

- Collectors: responsáveis por buscar dados externos
- Services: executam a lógica de negócio
- Repositories e database: armazenam e recuperam dados
- Providers: integram serviços externos, como o Gemini
- Telegram: envia os resumos para o chat configurado

### Principais componentes

- FastAPI: expõe os endpoints da API
- SQLAlchemy: modela e persiste os dados
- PostgreSQL: banco de dados principal
- Gemini: realiza a análise dos sinais
- Telegram Bot: envia o resumo final
- APScheduler: pode ser usado para automatizar execuções futuras

---

## 3. Fluxo atual do sistema

### Etapa 1: coleta de sinais

A aplicação busca sinais em três fontes principais:

- Notícias RSS
- Reddit
- Google Trends

Esses sinais são normalizados para um formato interno chamado Signal e passam a fazer parte do fluxo principal do projeto.

### Etapa 2: persistência

Os sinais coletados são salvos no banco PostgreSQL. Isso permite:

- evitar duplicidade
- manter histórico
- analisar apenas os sinais mais recentes
- usar os dados em etapas futuras do pipeline

### Etapa 3: análise com Gemini

Depois de coletar e salvar os sinais, o sistema envia esses dados ao Gemini para gerar uma análise semântica. O modelo identifica tópicos relevantes, atribui um score de relevância e sugere ideias de vídeo.

### Etapa 4: envio para Telegram

O resultado da análise pode ser convertido em uma mensagem formatada e enviada para um chat privado do Telegram, usando o token e o chat ID configurados.

---

## 4. Como os endpoints funcionam hoje

A API expõe endpoints para acionar cada parte do processo.

### Endpoint principal de saúde

- GET /health

Retorna se a aplicação está respondendo corretamente.

### Endpoint de coleta e ingestão

- POST /pipeline/collect-and-ingest

Esse endpoint executa:

- coleta de notícias, Reddit e trends
- normalização dos sinais
- persistência no banco

### Endpoint de análise

- POST /pipeline/analyze

Esse endpoint executa:

- leitura dos sinais recentes do banco
- envio destes sinais ao Gemini
- persistência dos resultados de análise

### Endpoint de teste do Gemini

- POST /pipeline/gemini-test

Serve para validar se o Gemini está respondendo corretamente.

### Endpoint de envio para Telegram

- POST /pipeline/send-telegram

Esse endpoint faz:

- buscar a análise mais recente
- montar a mensagem formatada
- enviar para o chat privado configurado no Telegram

### Endpoint de pipeline unificada

- POST /pipeline/run

Esse é o endpoint mais completo da versão atual. Ele orquestra, em uma única chamada, as etapas abaixo:

1. coleta dos sinais
2. ingestão no banco
3. análise com Gemini
4. envio da análise para o Telegram

Em outras palavras, ele funciona como um orquestrador simples do fluxo completo.

---

## 5. Fluxo recomendado em etapas

O sistema foi pensado para rodar em etapas. O modelo mais simples é o seguinte:

### Etapa A – Coleta

A aplicação busca sinais externos e os salva no banco.

### Etapa B – Análise

Os sinais recentes são enviados ao Gemini, que gera insights estruturados.

### Etapa C – Entrega

Os insights são transformados em uma mensagem e enviados ao Telegram.

Essa divisão deixa o processo mais claro, mais fácil de testar e mais robusto para falhas.

---

## 6. Como isso deveria rodar na nuvem

Quando o sistema for colocado em produção na nuvem, o ideal é que ele siga um fluxo parecido com o abaixo.

### Cenário ideal

1. A API sobe em um serviço web
2. O banco PostgreSQL fica disponível para a aplicação
3. O sistema recebe chamadas para executar a pipeline
4. As etapas são executadas em sequência
5. Os resultados ficam persistidos no banco
6. O Telegram recebe a mensagem final

### Estrutura sugerida na nuvem

- Serviço web: FastAPI
- Banco de dados: PostgreSQL
- Variáveis de ambiente: Gemini API Key, Telegram token, Telegram chat ID, DATABASE_URL
- Logs: para acompanhar falhas e sucesso
- Scheduler: para rodar a pipeline automaticamente em horário definido

### Fluxo em produção

Na nuvem, o processo ideal seria:

- a aplicação fica sempre disponível
- um scheduler dispara a execução da pipeline em intervalos regulares
- a pipeline faz coleta, análise e envio
- em caso de erro, o sistema registra o problema e não interrompe o restante do fluxo

---

## 7. O que já existe hoje

Hoje o projeto já possui:

- API rodando com FastAPI
- endpoints para coleta, análise e envio
- conexão com PostgreSQL
- persistência de sinais e análises
- integração com Gemini
- integração com Telegram
- pipeline unificada via /pipeline/run

---

## 8. O que ainda seria ideal evoluir

Para deixar o sistema mais robusto na nuvem, os próximos passos mais importantes seriam:

- adicionar um scheduler automático para rodar a pipeline diariamente
- separar melhor as falhas por etapa, por exemplo:
  - erro de coleta
  - erro de análise
  - erro de envio
- adicionar logs mais detalhados
- configurar health checks
- proteger o sistema com retries e tratamento de erro
- separar a execução em jobs assíncronos, se o volume crescer

---

## 9. Resumo simples

O sistema atual funciona assim:

- coleta sinais externos
- salva esses sinais no banco
- usa o Gemini para analisar tendências e oportunidades
- transforma isso em uma mensagem
- envia a mensagem ao Telegram

E o endpoint /pipeline/run representa a forma mais completa de executar tudo isso em uma única chamada.

Na nuvem, o ideal é que esse fluxo funcione de forma automatizada, em etapas, com a API como motor principal, o banco como armazenamento e um scheduler como gatilho para execução periódica.
