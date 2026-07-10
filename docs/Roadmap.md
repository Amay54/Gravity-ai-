# Development Roadmap - GravityAI

This document details the development milestones and release criteria for the GravityAI platform.

## Milestones Roadmap

### Phase 1: Project Initialization & Tooling
* **Goals**: Establish repositories, configure linters/formatters, specify Pydantic settings baselines, and initialize containerization profiles.
* **Status**: Completed (This step).

### Phase 2: Folder Structure Organization
* **Goals**: Create clean modular boundaries separating v1 API, agents, tools, databases, cache layers, and workflows.
* **Status**: Completed (This step).

### Phase 3: Docker Orchestration Setup
* **Goals**: Assemble multi-stage docker builds for Streamlit and FastAPI.
* **Status**: Completed (This step).

### Phase 4: FastAPI Server Framework
* **Goals**: Complete routing, global exception validation, request/response validation schemas, and system status routes.
* **Status**: In-Progress / Baseline Complete.

### Phase 5: Streamlit Dashboard UI
* **Goals**: Build dashboard layout, search interface, sidebar configurators, execution logs viewer, and report download buttons.
* **Status**: Pending.

### Phase 6: Supabase Cloud Database Integration
* **Goals**: Code database client classes, configure connection pools, map RLS rules, and write embedding table upload controllers.
* **Status**: Pending.

### Phase 7: Gemini LLM Integration
* **Goals**: Implement client libraries, configure tool invocation engines, map structure JSON outputs, and set up embedding generation pipelines.
* **Status**: Pending.

### Phase 8: Planner Agent & LangGraph Workflow
* **Goals**: Build the central graph, write state transitions, code routing nodes, and set up planner coordination agents.
* **Status**: Pending.

### Phase 9: Tool Registry & Core Scrapers
* **Goals**: Build tools for Search, Financial profiles, Competitors search, Technology scraper, and PDF rendering.
* **Status**: Pending.

### Phase 10: Special Workers (Research, Competitor, News, Finance, Technology, SWOT, Report, LinkedIn)
* **Goals**: Build specialized worker agents subdirectories inheriting from `BaseAgent`, tune prompts, and finalize system integration testing.
* **Status**: Pending.
