# Content Radar

O Content Radar acompanha o que está em alta no mercado literário e sugere ideias de vídeos curtos para YouTube, TikTok e Instagram Reels.

Todos os dias há conversas sobre livros espalhadas por portais de notícias, comunidades e buscas. O projeto reúne esses sinais, usa IA para identificar os temas com mais potencial e envia um resumo pelo Telegram. A análise dá peso extra ao mercado editorial brasileiro, sem deixar de lado tendências internacionais que podem influenciá-lo.

## Como funciona

```text
Notícias (RSS) ─┐
Reddit ─────────┼─> Coleta -> PostgreSQL -> Análise com Gemini -> Resumo no Telegram
Google Trends ──┘
```

1. **Coleta:** busca notícias, posts do Reddit e dados do Google Trends. As fontes ficam em [`app/config/sources.yaml`](app/config/sources.yaml).
2. **Armazenamento:** normaliza os sinais para um formato único, descarta duplicados e salva o restante no PostgreSQL.
3. **Análise:** envia os sinais recentes ao Gemini, com limite de volume por fonte. O modelo agrupa os assuntos relacionados, dá uma nota de 0 a 10 para cada tema e sugere 3 ideias de vídeo. O prompt está em [`app/prompts/daily_analysis.md`](app/prompts/daily_analysis.md).
4. **Entrega:** formata o resultado e envia para o chat do Telegram configurado.

Cada tema do resumo traz a nota, o motivo de ser relevante agora, a fonte de origem e as ideias de vídeo.

## Tecnologias

- **API:** Python e FastAPI
- **Banco de dados:** PostgreSQL, SQLAlchemy e Alembic
- **IA:** Google Gemini
- **Entrega:** Bot do Telegram

## Como rodar

Você vai precisar de Python 3.12 ou superior, PostgreSQL, uma chave da API do Gemini e um bot do Telegram com o ID do chat de destino.

1. Crie o ambiente virtual e instale as dependências:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. Copie o arquivo de exemplo e preencha o `.env`:

   ```powershell
   Copy-Item .env.example .env
   ```

   | Variável | Para que serve |
   |---|---|
   | `DATABASE_URL` | Conexão com o PostgreSQL |
   | `GEMINI_API_KEY` | Chave da API do Gemini |
   | `TELEGRAM_TOKEN` | Token do bot do Telegram |
   | `TELEGRAM_CHAT_ID` | Chat que recebe o resumo |
   | `PIPELINE_API_KEY` | Chave que protege as rotas `/pipeline/*` |

   Para gerar a `PIPELINE_API_KEY`:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. Crie as tabelas e suba a API:

   ```powershell
   alembic upgrade head
   uvicorn main:app --reload
   ```

4. Execute o fluxo completo:

   ```powershell
   curl.exe -X POST http://127.0.0.1:8000/pipeline/run -H "X-API-Key: sua_chave"
   ```

Para rodar o fluxo sem a API, use `python worker.py` ou, no Windows, `run_worker.bat`. Eles podem ser acionados por um agendador externo, como o Agendador de Tarefas do Windows.

## Rotas da API

As rotas `/pipeline/*` exigem o header `X-API-Key` com o valor de `PIPELINE_API_KEY`. Elas respondem `401` se a chave estiver errada ou ausente, e `503` se a variável não estiver configurada.

| Rota | O que faz |
|---|---|
| `GET /` | Confirma que a API está no ar |
| `GET /health` | Informa o status, o ambiente e o fuso horário |
| `POST /pipeline/run` | Executa o fluxo completo |
| `POST /pipeline/collect-and-ingest` | Coleta e salva os sinais |
| `POST /pipeline/analyze` | Analisa os sinais recentes |
| `POST /pipeline/send-telegram` | Gera uma nova análise e a envia pelo Telegram |
| `POST /pipeline/gemini-test` | Testa a integração com o Gemini |

## Estrutura do projeto

```text
app/
├── collectors/    # Coleta de notícias, Reddit e Google Trends
├── config/        # Configurações e lista de fontes
├── database/      # Conexão e manutenção do banco
├── models/        # Modelos de dados
├── prompts/       # Prompt da análise
├── providers/     # Integração com o Gemini
├── repositories/  # Acesso aos dados dos sinais
├── scheduler/     # Base para agendamento
├── services/      # Regras de cada etapa do fluxo
├── telegram/      # Formatação e envio das mensagens
└── utils/         # Funções auxiliares
alembic/           # Migrações do banco
tests/             # Testes automatizados
main.py            # API e rotas
worker.py          # Execução do fluxo sem a API
```

Mais detalhes em [`FUNCIONAMENTO_SISTEMA.md`](FUNCIONAMENTO_SISTEMA.md).

## Próximos passos

- Conectar o agendador interno ao fluxo, para que o resumo rode sozinho todos os dias. Hoje `ENABLE_SCHEDULER` só executa uma tarefa de exemplo.
- Ativar a limpeza automática dos dados antigos, usando `DATA_RETENTION_DAYS`.
