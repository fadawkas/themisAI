# ThemisAI

Web-based **Criminal Law Consultation & Follow-Up Recommendation System** using **Large Language Models (LLM)** + **Retrieval-Augmented Generation (RAG)** with **Indonesian legal sources** as grounded context.

> **Academic / Research Project** — Informatics, Faculty of Computer Science, UPN “Veteran” Jakarta


## Overview

**ThemisAI** helps users obtain **relevant, contextual, and traceable** information related to Indonesian criminal law.  
To reduce hallucinations, responses are generated using **RAG**: the system retrieves supporting legal documents (e.g., KUHP, KUHAP, related regulations) via semantic search and uses them as context for the LLM.


## Key Features

- **Chat-based legal consultation** (web UI)
- **RAG pipeline**: semantic retrieval → context injection → grounded generation
- **Document handling**: store & retrieve legal documents for context
- **User authentication**: sign up / sign in
- **Consultation history** stored in relational DB
- **Evaluation suite** with **RAGAS** (faithfulness, answer relevancy, context precision/recall)
- **Research modules** for RAG experiments + fine-tuning experiments


## System Architecture (High Level)

- **Frontend**: React + Vite + TypeScript (chat UI, auth pages)
- **Backend API**: FastAPI (auth, chat, docs, orchestration)
- **Retrieval Layer**: embeddings + FAISS vector index
- **Generation Layer**: LLM uses retrieved context to generate grounded responses
- **Relational DB**: PostgreSQL (users, chat history, metadata)
- **Evaluation**: RAGAS benchmarks + model comparisons (Gemma / Qwen / Llama experiments)


## Tech Stack

- **Backend**: Python, FastAPI, Alembic
- **Frontend**: React, TypeScript, Vite, Tailwind
- **Vector DB**: FAISS
- **Database**: PostgreSQL
- **Containerization**: Docker, Docker Compose
- **Evaluation**: RAGAS


## Repository Structure

```bash
themisAI/
├── backend/                # FastAPI backend + RAG pipeline + DB models
│   ├── app/
│   │   ├── core/           # config + security
│   │   ├── db/             # database, models, metadata files
│   │   ├── routers/        # auth, chat, documents
│   │   └── services/       # rag_engine, lawyer_rec, mailer, etc.
│   ├── alembic/            # migrations
│   └── uploads/            # uploaded docs (dev)
├── frontend/               # React web app (chat UI + auth)
├── rag_dev/                # RAG experiments (notebooks, scripts, outputs)
├── finetune_dev/           # Fine-tuning experiments (QLoRA notebooks, outputs)
├── benchmark/              # RAGAS evaluations + model comparison outputs
├── scraper/                # data collection + preprocessing utilities
├── haversine_dev/          # lawyer recommendation experiments
├── docker-compose.dev.yml  # dev environment
└── secrets_gen.py          # helper script (no sensitive files committed)
