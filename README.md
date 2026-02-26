# 🏗️ Gelişim Chatbot API — Production FastAPI Backend

Production-ready FastAPI backend for the Gelişim Pazarlama Chatbot. Built custom RAG logic for customer support.

## 🔒 Security Features

| Feature                | Description                         |
| ---------------------- | ----------------------------------- |
| **API Key Auth**       | `X-API-Key` header validation       |
| **Rate Limiting**      | 20 req/min per IP (slowapi + Redis) |
| **IP Daily Limit**     | 200 requests/day per IP             |
| **Global Daily Limit** | 5000 requests/day total             |
| **Input Limits**       | Max 1000 chars + 350 token estimate |
| **Prompt Injection**   | Regex pattern detection             |
| **CORS**               | Restricted to allowed origins       |
| **Body Size Limit**    | Max 10KB request body               |
| **Security Headers**   | HSTS, X-Frame-Options, etc.         |
| **Error Masking**      | No internal details in responses    |

## 📁 Project Structure

```
chatbot_fastapi/
├── app/
│   ├── main.py              # App factory + lifespan
│   ├── config.py             # Pydantic Settings
│   ├── api/v1/               # Routes (chat, health)
│   ├── core/                 # Security, rate/budget limiter
│   ├── middleware/            # CORS, headers, error handler
│   ├── models/               # Pydantic request/response
│   ├── services/             # Search, LLM, chat pipeline
│   └── utils/                # Cache, text sanitizer
├── tests/                    # Pytest tests
├── Dockerfile                # Production container
├── docker-compose.yml        # Local dev (API + Redis)
├── railway.json              # Railway deployment
└── requirements.txt          # Pinned dependencies
```

## 🚀 Quick Start

### 1. Setup

```bash
cd chatbot_fastapi
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your real API keys
```

### 3. Start Redis (Required)

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

### 4. Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Test

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Chat (requires API key)
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"query": "Pepsi ürünleri nelerdir?"}'
```

## 🐳 Docker

```bash
docker compose up --build
```

## 🚂 Deploy to Railway

1. Push code to GitHub
2. Connect repo on Railway
3. Add Redis service on Railway
4. Set environment variables in Railway dashboard
5. Deploy — Railway handles SSL, domains, and scaling automatically

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 📡 API Endpoints

| Method | Path                  | Description             | Auth        |
| ------ | --------------------- | ----------------------- | ----------- |
| `POST` | `/api/v1/chat`        | Send a chat message     | `X-API-Key` |
| `POST` | `/api/v1/chat/stream` | Chat with SSE streaming | `X-API-Key` |
| `GET`  | `/api/v1/health`      | Health check            | None        |
