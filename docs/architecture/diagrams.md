# GravityAI Architecture Diagrams

This handbook compiles architectural specifications and structural diagrams detailing the GravityAI AI Research Operating System.

---

## 1. System Architecture Diagram

```mermaid
graph TD
    User([User Client]) <-->|Streamlit Dashboard| Frontend[Streamlit Container: 8501]
    Frontend <-->|REST HTTP / OpenAPI| Gateway[FastAPI Gateway Container: 8000]
    Gateway <-->|Workflow Execution| Planner[Planner Agent / LangGraph Graph]
    Planner <-->|Bus Messages / State| Specialists[Specialist Agents: Finance, Market, Tech, Hiring, Reviewer]
    Specialists <-->|Scraper Requests| Tools[Tool Registry / Scraper Nodes]
    Tools -->|Gemini API Queries| Gemini[Google Gemini 2.5 Flash]
    Gateway <-->|CRUD & SQL Queries| DB[(Supabase Cloud Database)]
    Gateway <-->|Signed URL Upload/Download| Storage[(Supabase Storage Buckets)]
```

---

## 2. Agent Collaboration & Bus Architecture

```mermaid
graph LR
    Manager[Research Manager Agent] -->|Message Bus| Bus{Agent Message Bus}
    Bus -->|Orchestrate Node| Finance[Financial Analyst Agent]
    Bus -->|Orchestrate Node| Market[Market Analyst Agent]
    Bus -->|Orchestrate Node| Tech[Technology Analyst Agent]
    Bus -->|Orchestrate Node| Hiring[Hiring Analyst Agent]
    
    Finance -->|Factual Synthesis| Manager
    Market -->|Factual Synthesis| Manager
    Tech -->|Factual Synthesis| Manager
    Hiring -->|Factual Synthesis| Manager
    
    Manager -->|Final Dossier Audit| Reviewer[Report Reviewer Agent]
    Reviewer -->|Self-Correction loop if gaps| Bus
```

---

## 3. Tool Calling Flow

```mermaid
sequenceDiagram
    participant Agent as Specialist Agent
    participant Registry as Tool Registry
    participant Cache as Cache Manager
    participant External as External Scrapers / APIs
    
    Agent->>Registry: execute_tool(name, params)
    Registry->>Cache: Check tool cache (lookup parameters hash)
    alt Cache Hit
        Cache-->>Registry: Return cached ToolResponse
        Registry-->>Agent: Return response (cache_hit=True)
    else Cache Miss
        Registry->>External: Fire network scraper query
        External-->>Registry: Return raw parsed result payload
        Registry->>Cache: Save tool result in cache
        Registry-->>Agent: Return response (cache_hit=False)
    end
```

---

## 4. Export & Compilation Flow

```mermaid
graph TD
    Client[FastAPI Endpoint] -->|Export Request| Service[Export Service Queue]
    Service -->|Aggregate Store| Evidence[Evidence Store Citation Resolver]
    Service -->|Chart Definition| Matplotlib[Visualisation Engine: Matplotlib]
    
    Service -->|Generate| PDF[ReportLab PDF Canvas]
    Service -->|Generate| DOCX[python-docx Word Builder]
    Service -->|Generate| PPTX[python-pptx PowerPoint Builder]
    Service -->|Generate| HTML[Responsive HTML Layout]
    Service -->|Generate| MD[Markdown Writer]
    
    PDF -->|Upload| Supabase[(Supabase Storage)]
    DOCX -->|Upload| Supabase
    PPTX -->|Upload| Supabase
    HTML -->|Upload| Supabase
    MD -->|Upload| Supabase
    
    Supabase -->|Signed URL| Client
```

---

## 5. Content Generation & Publishing Safety Gate Flow

```mermaid
graph TD
    Report[Research Report Object] -->|Input| Engine[Content Generation Engine]
    Engine -->|Select Tone/Style| Synthesis[LLM Text Synthesis / Template Fallback]
    Synthesis -->|Output Draft| Audit[AI Quality Checker / Readability Audit]
    Audit -->|Save| Db[(Content Drafts Repository)]
    
    Db -->|View Draft| Preview[UI Dashboard Draft Preview]
    Preview -->|Check Confirm Box| Gate{User Authorization Box Checked?}
    Gate -->|No| PublishDisabled[Publish Action Button Disabled]
    Gate -->|Yes| PublishEnabled[Publish Action Button Enabled]
    
    PublishEnabled -->|Trigger Publish| Connector[Social Publishing Connectors]
    Connector -->|Publish Feed Post| LinkedIn[LinkedIn Feed]
    Connector -->|Publish Feed Post| Twitter[X Twitter Feed]
    Connector -->|Publish Feed Post| Medium[Medium publication]
```
