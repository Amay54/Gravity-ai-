# Software Requirements Specification (SRS) - GravityAI

## 1. Introduction

### 1.1 Purpose
This document details the functional and non-functional requirements for **GravityAI**, an enterprise-grade AI Research Operating System designed to automate end-to-end corporate intelligence gathering, competitor evaluation, financial analysis, SWOT assessment, and multi-format report generation.

### 1.2 Scope
GravityAI acts as a centralized research workspace containing a Streamlit frontend that talks exclusively to a FastAPI backend. The backend manages a pool of AI agents coordinated by a Planner Agent running a LangGraph workflow. The application features Supabase integration for security, audit logging, data persistence, and semantic vector storage.

---

## 2. Overall Description

```
                     ┌──────────────────┐
                     │    User (UI)     │
                     └────────┬─────────┘
                              │ REST API
                     ┌────────▼─────────┐
                     │ FastAPI Backend  │
                     └────────┬─────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Planner Agent   │
                    └─────────┬─────────┘
                              │ Workflow Routing
                    ┌─────────▼─────────┐
                    │ LangGraph Orchest │
                    └────┬──────────┬───┘
                         │          │
         ┌───────────────▼──┐    ┌──▼────────────────┐
         │ Research Agent   │    │ SWOT/Report Agent │
         └───────┬──────────┘    └────┬──────────────┘
                 │                    │
         ┌───────▼──────────┐    ┌────▼──────────────┐
         │  Tool Registry   │    │  Supabase Cloud   │
         └──────────────────┘    └───────────────────┘
```

### 2.1 Core Subsystems
1. **Streamlit Frontend**: Dashboard UI containing visual progress trackers, agent logs, search terminals, and downloaders.
2. **FastAPI Backend Router**: High-throughput REST API with versioned endpoints (`/api/v1`).
3. **Planner Agent**: Interprets company research requests, compiles execution paths, and lists agents & tools to summon.
4. **LangGraph Workflow Engine**: Controls state transitions, handles agent execution loops, and ensures error resilience.
5. **Tool Registry**: Dynamic discovery hub exposing modular interfaces for web search, financial databases, technology scrapers, and PDF compilers.
6. **Supabase Cloud System**: Storage of auth states, company report histories, system logs, and semantic research vectors.

---

## 3. Functional Requirements

### 3.1 Company Search & Agent Triggering
- **Input**: Target Company Name, Domain Name, Research Depth.
- **Workflow**: 
  - FastAPI verifies request inputs and saves a research state block in Supabase.
  - The Planner Agent maps the research tasks into a Graph state.
  - Sub-agents are triggered concurrently or sequentially as dictated by the plan.
  - Real-time logging of tool executions is pushed to Supabase and queryable by the frontend.

### 3.2 Specialist AI Agents
- **Research Agent**: Collects business profile, headquarters, division breakdown, mission, and products.
- **Competitor Agent**: Finds top direct and indirect competitors, comparing size, funding, and focus.
- **News Agent**: Discovers recent press releases, acquisitions, funding rounds, and partnerships.
- **Finance Agent**: Retrieves revenue, funding stages, valuation, or key public financial ratios.
- **Technology Agent**: Performs website scrapings to detect tech stack frameworks and hosting properties.
- **SWOT Agent**: Processes gathered agent outputs into a structured Strengths, Weaknesses, Opportunities, and Threats matrix.
- **Report Agent**: Synthesizes the aggregated findings into a single coherent markdown dataset.
- **LinkedIn Agent**: Crafts personalized LinkedIn posts matching professional branding layouts.

### 3.3 Output and File Compilation
- **PDF Compiler**: Generates professional PDF files containing formatted summaries, tables, and branding headers.
- **Social Media Assistant**: Presents ready-to-copy LinkedIn posts in the frontend UI with formatting.

---

## 4. Non-Functional Requirements

### 4.1 Security & Auth
- JWT authentication for all backend API accesses.
- Row Level Security (RLS) enabled on all Supabase tables, restricting researchers to their own queries.

### 4.2 Reliability & Fault Tolerance
- All tool failures must result in fallback actions (e.g., partial results) without causing graph crashes.
- Pydantic models validate all inputs/outputs at network boundaries.
- Database writing operations must handle connection timeouts gracefully with custom retries.
