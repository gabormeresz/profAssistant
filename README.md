<p align="center">
  <h1 align="center">🎓 ProfAssistant</h1>
  <p align="center">
    <strong>AI-Powered Educational Content Generator for Higher Education</strong>
  </p>
  <p align="center">
    Built with LangGraph · FastAPI · React · OpenAI
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-0.119+-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LangGraph-1.0+-1C3C3C?logo=langchain&logoColor=white" alt="LangGraph" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white" alt="Docker" />
</p>

---

## 📖 Overview

**ProfAssistant** is a full-stack AI assistant that helps university professors and educators generate high-quality educational content. It leverages **LangGraph** agentic workflows with built-in evaluation loops to produce course outlines, lesson plans, and presentations — iteratively refining each output until it meets quality thresholds.

The system uses a **generate → evaluate → refine** loop powered by specialized AI agents, supports document uploads for RAG-based context, and integrates external knowledge sources via the **Model Context Protocol (MCP)**.

---

## ✨ Features

### 🧠 Agentic Content Generation

- **Course Outline Generator** — Produces structured semester-long course outlines with topics, learning objectives, and activities
- **Lesson Plan Generator** — Creates detailed lesson plans for individual classes with timing, exercises, and assessments
- **Presentation Generator** — Generates slide decks with exportable PowerPoint (.pptx) download
- **Assessment Generator** — _(In progress)_ Creates quizzes, exams, and evaluation materials

### 🔄 Quality Assurance Loop

Each generation workflow follows a multi-step agentic pipeline:

1. **Initialize** — Load conversation context and metadata
2. **Build Messages** — Construct the prompt with history and user input
3. **Generate** — LLM produces initial content with tool access
4. **Evaluate** — A separate evaluator agent scores quality (0.0–1.0) across multiple dimensions
5. **Refine** — If the score is below the threshold (0.8), the content is refined using evaluation feedback
6. **Respond** — Final structured output is returned when approved or after max retries

### 📄 Document Upload & RAG

- Upload PDF, DOCX, or plain text files as reference material
- Documents are chunked and stored in **ChromaDB** with OpenAI embeddings
- Agents can search uploaded documents during generation for contextually relevant content

### 🌐 External Knowledge (MCP)

- Integrated **Wikipedia MCP server** for real-time factual research
- **Web Search** tool (Google Serper) for current information
- Extensible MCP architecture — add more knowledge sources easily

### 🎨 Smart Prompt Enhancement

- Built-in prompt enhancer that transforms basic user instructions into clear, specific, pedagogically-informed prompts

### 🔐 Authentication & Multi-User

- JWT-based authentication with access and refresh tokens
- Per-user API key management (encrypted at rest)
- User-selectable OpenAI models (GPT-4o Mini through GPT-5.2)
- Conversation history with save/load functionality

### 🌍 Internationalization

- Full i18n support with **English** and **Hungarian** locales
- Language-aware content generation

### 📊 Real-Time Streaming

- Server-Sent Events (SSE) for live generation progress
- Step-by-step visibility into the agent's workflow (initializing → researching → generating → evaluating → refining → complete)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Frontend                               │
│                React 19 · Tailwind CSS · Vite                   │
│                                                                 │
│  ┌───────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │  Course   │ │  Lesson  │ │ Presentation │ │  Assessment  │   │
│  │  Outline  │ │   Plan   │ │  Generator   │ │  Generator   │   │
│  └─────┬─────┘ └─────┬────┘ └──────┬───────┘ └──────┬───────┘   │
│        └─────────────┴─────────────┴────────────────┘           │
│                             │ SSE                               │
└─────────────────────────────┼───────────────────────────────────┘
                              │
┌─────────────────────────────┼───────────────────────────────────┐
│                       FastAPI Backend                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │               LangGraph Agent Workflows                   │  │
│  │                                                           │  │
│  │   ┌──────────┐     ┌──────────┐     ┌──────────┐          │  │
│  │   │ Generate │───▶│ Evaluate │────▶│  Refine  │          │  │
│  │   └────┬─────┘     └───▲──────┘     └───┬─┬────┘          │  │
│  │        │               │                │ │               │  │
│  │        │               └────────────────┘ │               │  │
│  │        │           (refine-evaluate loop) │               │  │
│  │        │                                  │               │  │
│  │   ┌────▼─────┐                      ┌─────▼────┐          │  │
│  │   │  Tools   │                      │  Tools   │          │  │
│  │   │(generate)│                      │ (refine) │          │  │
│  │   └────┬─────┘                      └────┬─────┘          │  │
│  │        │          ┌────────────┐         │                │  │
│  │        ├─────────▶│ Web Search │◀───────┤                │  │
│  │        │          │  (Serper)  │         │                │  │
│  │        │          └────────────┘         │                │  │
│  │        │          ┌────────────┐         │                │  │
│  │        ├─────────▶│ Wikipedia  │◀───────┤                │  │
│  │        │          │   (MCP)    │         │                │  │
│  │        │          └────────────┘         │                │  │
│  │        │          ┌────────────┐         │                │  │
│  │        └─────────▶│    RAG     │◀───────┘                │  │
│  │                   │ (ChromaDB) │                          │  │
│  │                   └────────────┘                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────┐             │
│  │   Auth    │  │  SQLite   │  │  PPTX Generator  │             │
│  │   (JWT)   │  │    DBs    │  │  (python-pptx)   │             │
│  └───────────┘  └───────────┘  └──────────────────┘             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│                   MCP Server (Wikipedia)                        │
│                   SSE Transport · Port 8765                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
profassistant/
├── docker-compose.yml          # Local development compose
├── docker-compose.prod.yml     # Production overrides
│
├── backend/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Centralized configuration
│   ├── Dockerfile              # Backend multi-stage build
│   ├── Dockerfile.mcp          # Wikipedia MCP server image
│   ├── pyproject.toml          # Python dependencies (uv)
│   │
│   ├── agent/                  # LangGraph agentic workflows
│   │   ├── base/               # Shared state, nodes, routing logic
│   │   │   ├── state.py        # Base state definitions
│   │   │   └── nodes/          # Reusable graph nodes
│   │   ├── course_outline/     # Course outline generation graph
│   │   ├── lesson_plan/        # Lesson plan generation graph
│   │   ├── presentation/       # Presentation generation graph
│   │   ├── model.py            # LLM model factory with presets
│   │   ├── prompt_enhancer.py  # Intelligent prompt enhancement
│   │   ├── tool_config.py      # Tool binding configuration
│   │   └── tools.py            # Web search & RAG search tools
│   │
│   ├── routes/                 # FastAPI route modules
│   │   ├── auth.py             # Registration, login, token refresh
│   │   ├── generation.py       # SSE endpoints for content generation
│   │   └── conversations.py    # Conversation CRUD & history
│   │
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py     # JWT token management
│   │   ├── database.py         # SQLite connection manager
│   │   ├── mcp_client.py       # MCP server client manager
│   │   ├── pptx_service.py     # PowerPoint file generation
│   │   └── rag_pipeline.py     # ChromaDB RAG pipeline
│   │
│   ├── schemas/                # Pydantic models
│   └── utils/                  # SSE helpers, file processing
│
└── frontend/
    ├── Dockerfile              # Multi-stage build (Vite → Nginx)
    ├── nginx.conf              # Nginx config with API reverse proxy
    ├── package.json            # Node.js dependencies
    │
    └── src/
        ├── App.tsx             # React Router configuration
        ├── pages/              # Page components
        ├── components/         # Reusable UI components
        ├── contexts/           # Auth & conversation contexts
        ├── hooks/              # Custom React hooks (SSE, export, etc.)
        ├── services/           # API client services
        ├── i18n/               # Internationalization (en, hu)
        └── types/              # TypeScript type definitions
```

---

## 🚀 Getting Started

### Prerequisites

| Tool                              | Version | Purpose                             |
| --------------------------------- | ------- | ----------------------------------- |
| [Python](https://www.python.org/) | 3.12+   | Backend runtime                     |
| [uv](https://docs.astral.sh/uv/)  | latest  | Fast Python package manager         |
| [Node.js](https://nodejs.org/)    | 22+     | Frontend build toolchain            |
| [Docker](https://www.docker.com/) | 24+     | Containerized deployment (optional) |

### API Keys Required

| Service                                                | Required    | Purpose                     |
| ------------------------------------------------------ | ----------- | --------------------------- |
| [OpenAI API Key](https://platform.openai.com/api-keys) | ✅ Yes      | LLM generation & embeddings |
| [Google Serper API Key](https://serper.dev/)           | ⚡ Optional | Web search tool             |

---

## 🖥️ Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/profassistant.git
cd profassistant
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies with uv
uv sync

# Create your environment file from the template
cp .env.example .env
```

Edit `backend/.env` and fill in your values. The example file is fully commented — at minimum you need to set:

- **`OPENAI_API_KEY`** — Your OpenAI API key (required for all generation)
- **`JWT_SECRET`** & **`ENCRYPTION_KEY`** — Auth secrets (the `.env.example` includes a one-liner to generate both)
- **`ADMIN_EMAIL`** & **`ADMIN_PASSWORD`** — Seed admin account created on first startup
- **`SERPER_API_KEY`** — _(optional)_ Enables the web search tool

> 💡 **Tip:** Generate secure auth keys in one command:
>
> ```bash
> python3 -c "import secrets,base64,os; print('JWT_SECRET=' + secrets.token_hex(32)); print('ENCRYPTION_KEY=' + base64.urlsafe_b64encode(os.urandom(32)).decode())"
> ```

### 3. Start the Wikipedia MCP Server

```bash
cd backend
uv run wikipedia-mcp --transport sse --port 8765 --enable-cache
```

### 4. Start the Backend

In a new terminal:

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

The API will be available at **http://localhost:8000** (docs at `/docs`).

### 5. Frontend Setup

In a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at **http://localhost:5173**.

---

## 🐳 Docker Setup

Docker Compose spins up all three services (frontend, backend, MCP server) in one command.

### 1. Create the Environment File

```bash
# Copy the template and fill in your values
cp .env.docker.example .env.docker
```

The template is fully documented — see `.env.docker.example` for all available options. The required keys are the same as for local development (`OPENAI_API_KEY`, `JWT_SECRET`, `ENCRYPTION_KEY`, admin credentials).

> **Note:** Docker-internal settings like `MCP_WIKIPEDIA_URL` are already configured in `docker-compose.yml` — you don't need to set them in `.env.docker`.

### 2. Build & Start (Development)

```bash
docker compose up --build
```

| Service       | URL                              |
| ------------- | -------------------------------- |
| Frontend      | http://localhost:3000            |
| Backend API   | http://localhost:8000            |
| MCP Wikipedia | http://localhost:8765 (internal) |

### 3. Build & Start (Production)

The production setup uses Nginx as a reverse proxy, exposing only port 80:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

| Service         | URL                        |
| --------------- | -------------------------- |
| Application     | http://localhost (port 80) |
| API (via proxy) | http://localhost/api/      |

> **Security note:** The production compose file already sets `COOKIE_SECURE=true` and `COOKIE_SAMESITE=strict` for secure refresh-token cookies. If you're deploying under a custom domain, also set `COOKIE_DOMAIN=yourdomain.com` in your `.env.docker` or uncomment it in `docker-compose.prod.yml`.

### 4. Stop & Clean Up

```bash
# Stop all services
docker compose down

# Stop and remove volumes (⚠️ deletes databases)
docker compose down -v
```

---

## ⚙️ Configuration Reference

All backend settings are centralized in `backend/config.py`:

| Config Class         | Key Settings                                                 | Env Vars                                                                                                             |
| -------------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| **RAGConfig**        | Chunk size (500), overlap (100), embedding model             | `DATA_DIR`                                                                                                           |
| **LLMConfig**        | Available models, presets, reasoning models                  | —                                                                                                                    |
| **APIConfig**        | CORS origins                                                 | `CORS_ORIGINS`                                                                                                       |
| **DBConfig**         | SQLite paths for conversations & checkpoints                 | `DATA_DIR`                                                                                                           |
| **AuthConfig**       | JWT secret, token expiry, admin credentials, cookie settings | `JWT_SECRET`, `ENCRYPTION_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `COOKIE_SECURE`, `COOKIE_SAMESITE`, `COOKIE_DOMAIN` |
| **EvaluationConfig** | Approval threshold (0.8), max retries (3), dimension weights | —                                                                                                                    |
| **UploadConfig**     | Maximum file upload size (default: 10 MB)                    | `MAX_FILE_SIZE`                                                                                                      |
| **MCPConfig**        | Wikipedia server URL & transport                             | `MCP_WIKIPEDIA_ENABLED`, `MCP_WIKIPEDIA_URL`                                                                         |
| **DebugConfig**      | Dummy graph toggle for testing (course outline only)         | `USE_DUMMY_GRAPH`                                                                                                    |
| **LoggingConfig**    | Log level                                                    | `LOG_LEVEL`                                                                                                          |

---

## 🔧 Available OpenAI Models

Users can select their preferred model in the profile page:

| Model        | Type      | Best For                              |
| ------------ | --------- | ------------------------------------- |
| GPT-4o Mini  | Standard  | Fast, cost-effective generation       |
| GPT-4.1 Mini | Standard  | Balanced performance                  |
| GPT-5 Mini   | Reasoning | Complex content with chain-of-thought |
| GPT-5        | Reasoning | High-quality generation               |
| GPT-5.2      | Reasoning | Best quality, higher cost             |

> **Note:** Reasoning models use `reasoning_effort` instead of `temperature` — this is handled automatically.

---

## 🛠️ Development

### Backend

```bash
cd backend

# Run with auto-reload
uv run uvicorn main:app --reload --port 8000

# Clean databases (reset conversations & checkpoints)
uv run python clean_databases.py
```

### Frontend

```bash
cd frontend

# Development server with HMR
npm run dev

# Type check + production build
npm run build

# Lint
npm run lint

# Preview production build
npm run preview
```

---

## 📡 API Endpoints

| Method | Endpoint                   | Description                              |
| ------ | -------------------------- | ---------------------------------------- |
| `POST` | `/auth/register`           | Register a new user                      |
| `POST` | `/auth/login`              | Login and receive tokens                 |
| `POST` | `/auth/refresh`            | Refresh access token                     |
| `POST` | `/enhance-prompt`          | Enhance a user prompt with AI            |
| `POST` | `/generate-course-outline` | Generate course outline (SSE stream)     |
| `POST` | `/generate-lesson-plan`    | Generate lesson plan (SSE stream)        |
| `POST` | `/generate-presentation`   | Generate presentation (SSE stream)       |
| `POST` | `/download-pptx`           | Download generated presentation as .pptx |
| `GET`  | `/conversations`           | List saved conversations                 |
| `GET`  | `/conversations/{id}`      | Load a specific conversation             |

> Full interactive API docs available at **http://localhost:8000/docs** when running locally.
>
> **Production note:** Swagger, ReDoc, and the OpenAPI schema are automatically disabled when `LOG_LEVEL` is set to `WARNING` or higher. Authentication endpoints are rate-limited (login: 5/min, register: 3/min, refresh: 10/min).

---

## 🤝 Tech Stack

| Layer            | Technology                                                   |
| ---------------- | ------------------------------------------------------------ |
| **Frontend**     | React 19, TypeScript, Tailwind CSS 4, Vite 7, React Router 7 |
| **Backend**      | Python 3.12, FastAPI, Pydantic v2, uvicorn                   |
| **AI/Agents**    | LangGraph, LangChain, OpenAI API                             |
| **Vector DB**    | ChromaDB (embedded, persistent)                              |
| **Database**     | SQLite (async via aiosqlite)                                 |
| **Auth**         | JWT (PyJWT), bcrypt, Fernet encryption                       |
| **MCP**          | Wikipedia MCP server (SSE transport)                         |
| **Export**       | python-pptx (PowerPoint generation)                          |
| **i18n**         | i18next, react-i18next (EN, HU)                              |
| **Package Mgmt** | uv (Python), npm (Node.js)                                   |
| **Deployment**   | Docker, Docker Compose, Nginx                                |

---

## 📜 License

This project was developed as a **diploma thesis** (diplomamunka).

Licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made with ❤️ for educators
</p>
