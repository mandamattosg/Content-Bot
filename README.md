# Content Radar

Projeto para coletar sinais de noticias, Reddit e Google Trends sobre o mercado literario, analisar com Gemini e enviar resumo no Telegram.

## Sprint 1 implementada

- Estrutura inicial em camadas
- API FastAPI com endpoint de healthcheck
- Configuracao centralizada com pydantic-settings
- Scheduler base com APScheduler (job placeholder)
- Arquivos de ambiente e fontes iniciais

## Sprint 2 implementada

- Modelos SQLAlchemy para `signals`, `analysis_runs` e `topic_summaries`
- Configuracao de sessao/engine em `app/database/session.py`
- Alembic inicializado com migracao inicial
- Politica de retencao configuravel (`DATA_RETENTION_DAYS`, padrao 15)

## Sprint 3 implementada

- Interface base de collector em `app/collectors/base.py`
- NewsCollector com RSS e retries
- RedditCollector com JSON publico e retries
- TrendsCollector com pytrends e retries
- Fontes configuraveis em `app/config/sources.yaml`
- Normalizacao de saida para o modelo `Signal`

## Sprint 4 implementada

- Normalizacao e compactacao de sinais em `app/services/signal_normalizer.py`
- Hash de conteudo para deduplicacao em `app/utils/signal_hash.py`
- Limites de volume por fonte antes da IA
- Payload final reduzido para analise com o Gemini

## Sprint 5 implementada

- Persistencia com deduplicacao em `app/repositories/signal_repository.py`
- Servico de ingestao em `app/services/signal_ingestion.py`
- Endpoint manual para executar coleta e persistencia: `POST /pipeline/collect-and-ingest`
- Deduplicacao por URL, titulo+data e hash de conteudo

## Requisitos

- Python 3.12+
- PostgreSQL (sera usado nas proximas sprints)

## Como rodar local

1. Criar e ativar ambiente virtual:

### PowerShell (Windows)

```powershell
cd content-radar
.\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias:

```powershell
pip install -r requirements.txt
```

3. Ajustar variaveis no arquivo `.env`.

4. Subir API:

```powershell
uvicorn main:app --reload
```

5. Verificar:

- `GET http://127.0.0.1:8000/`
- `GET http://127.0.0.1:8000/health`

## Banco de dados (Sprint 2)

Com PostgreSQL rodando e `DATABASE_URL` configurada no `.env`:

```powershell
cd content-radar
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

## Sprint 6 implementada

- Provider abstrato de IA em `app/providers/base.py`
- Implementacao do Gemini em `app/providers/gemini.py`
- Prompt separado em `app/prompts/daily_analysis.md`
- Servico de analise de sinais recentes em `app/services/analysis_service.py`
- Endpoint manual para executar analise: `POST /pipeline/analyze`
- Persistencia de `analysis_runs` e `topic_summaries` no banco

## Como executar a analise

1. Configure `GEMINI_API_KEY` no `.env`.
2. Execute o fluxo de ingestao para salvar sinais recentes.
3. Chame o endpoint:

```powershell
curl -X POST http://127.0.0.1:8000/pipeline/analyze
```

## Proximos passos

- Sprint 7: Telegram com resumo bonito
- Sprint 8: scheduler diario

## Telegram

Para enviar o resumo somente para o seu chat privado, configure no `.env`:

```env
TELEGRAM_TOKEN=seu_token_do_bot
TELEGRAM_CHAT_ID=seu_chat_id
```

O bot envia a mensagem apenas para o `chat_id` configurado, não para grupos ou chats públicos.
