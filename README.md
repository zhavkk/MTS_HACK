
# Multistage Agent System

An intelligent modular agent system designed to process client queries, generate responses, and provide recommendations to a human operator.

---

## ⚙️ Tech Stack

| Backend  | UI       | Infrastructure | Memory |
|----------|----------|----------------|--------|
| FastAPI  | Streamlit| Docker         | Redis  |

---

## 🧩 Architecture Overview

### 🧠 Orchestrator

Coordinates interactions between agents and manages memory and external API endpoints:

- Interfaces with agents and Redis.
- Implements memory mechanisms for agent context.
- Performs validation and summarization of agent requests.
- Exposes an API for integration with other services.
- Controls the sequence of agent execution.

---

### 🤖 Agents

| Agent               | Purpose |
|---------------------|---------|
| 🎭 **Emotion + Intent** | Detects the client's emotion and intent. |
| 📚 **Knowledge Agent** | Retrieves relevant information from the knowledge base. |
| 💡 **Action Suggestion** | Generates recommendations for the operator. |
| 🧾 **Summary + QAA** | Creates summaries and performs quality assessment. |

---

## 🚀 Quick Start Guide

### 🐳 Docker Setup
```bash
docker compose up --build -d
```

### ▶️ Run Clients
```bash
python3 client.py 
```
Visit [http://localhost:8501/](http://localhost:8501/), copy the hash to the client, input a message, and wait for the system to respond.

---

## 🔐 Environment Variables

A valid API key is required for agent communication:

```
MWS_API_KEY=<your_api_key>
```

Make sure to set this in each agent’s `.env` file.

---

## 📚 Custom Vector Database (VD) Generation

To build a custom vector database for the RAG agent:

1. Prepare an Excel file (`.xlsx`) with the following columns:
   - `query`
   - `correct_answer`
   - `sources`

2. Run the build script:
```bash
python3 rag-agent/app/build_vd.py
```

---

