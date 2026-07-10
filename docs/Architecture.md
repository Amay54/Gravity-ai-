# System Architecture Design - GravityAI

This document outlines the system architecture, component layout, and data-flow pathways of the GravityAI Enterprise AI Research Operating System.

## 1. High-Level Architecture Diagram

```mermaid
graph TD
    UI[Streamlit Dashboard]
    API[FastAPI Gateway]
    DB[(Supabase PostgreSQL)]
    PLAN[Planner Agent]
    REG[Tool Registry]
    GEMINI[Google Gemini 2.5 Flash]
    
    UI -->|HTTPS REST| API
    API -->|Read/Write| DB
    API -->|Execute Graph| PLAN
    
    subgraph Agent Subsystem (LangGraph Workflow)
        PLAN -->|State Router| R_AGT[Research Agent]
        PLAN -->|State Router| C_AGT[Competitor Agent]
        PLAN -->|State Router| N_AGT[News Agent]
        PLAN -->|State Router| F_AGT[Finance Agent]
        
        R_AGT -->|Call Tool| REG
        C_AGT -->|Call Tool| REG
        N_AGT -->|Call Tool| REG
        F_AGT -->|Call Tool| REG
    end
    
    REG -->|Structured API Calls| GEMINI
    REG -->|Save Log| DB
```

---

## 2. Core Modules

### 2.1 Backend Gateway (FastAPI)
The backend operates as an asynchronous FastAPI server.
* **API Versioning**: All routing resides under `/api/v1` to ensure backward compatibility.
* **Worker Execution**: Research tasks are non-blocking. Initiating a research request spins up a background thread/task via `FastAPI.BackgroundTasks` so the API client receives a tracking ID immediately.
* **Configuration Layer**: Employs Pydantic settings matching the `.env` configuration file structure.

### 2.2 Orchestration Engine (LangGraph)
Uses LangGraph to define a state-machine diagram representing research progress:
1. **Initialize State**: Setup company profile records.
2. **Planner Routing**: The Planner Agent inspects user request context to determine necessary agent node operations.
3. **Parallel Sub-Agent Execution**: Sub-agents (Research, Competitor, News, Finance) execute their respective loops in parallel nodes.
4. **Aggregation Node**: Combines outputs into a unified report context.
5. **Synthesis Nodes**: Invokes SWOT synthesis, PDF layout compile, and LinkedIn content formatting.
6. **Persistence**: Saves state snapshots directly to Supabase.

### 2.3 Tool Calling & Registry
To prevent prompt injection risks and guarantee determinism, agents do not write scripts on-the-fly. They request structured tools from the `Tool Registry`.
* **Registry Structure**: Dynamically tracks tools matching the `BaseTool` schema.
* **Gemini Tool Calling**: Converts Python Pydantic definitions of inputs into OpenAI/Gemini schema arguments, prompting Gemini to output JSON matches, which the Tool Registry decodes and runs.

### 2.4 Supabase Storage
Direct connections to Supabase Cloud host data persistence:
* **Research Log Tables**: Track progress logs that Streamlit UI polls.
* **Vector Embeddings**: Store company textual logs mapped into a 1536-dimension float space for semantic cross-referencing.
