# Database Schema Design - GravityAI

This document describes the schema design for the Supabase Cloud PostgreSQL database, aligned with the actual repository queries in the GravityAI application.

---

## 1. Schema Diagram Overview

```
 ┌────────────────────────┐        ┌────────────────────────┐
 │       auth.users       │        │   research_sessions    │
 ├────────────────────────┤        ├────────────────────────┤
 │ id (PK, UUID)          │◄───────│ id (PK, UUID)          │
 └────────────────────────┘        │ user_id (FK, TEXT/UUID)│
                                   │ company_name (TEXT)    │
                                   │ status (TEXT)          │
                                   └──────────┬─────────────┘
                                              │
         ┌────────────────────────────────────┼───────────────────────────────────┐
         │ 1:Many                             │ 1:Many                            │ 1:Many
 ┌───────▼─────────────────┐        ┌─────────▼──────────────┐          ┌──────────▼──────────────┐
 │ research_execution_logs │        │  tool_execution_logs   │          │    research_reports     │
 ├─────────────────────────┤        ├────────────────────────┤          ├─────────────────────────┤
 │ id (PK, UUID)           │        │ id (PK, UUID)          │          │ id (PK, UUID)           │
 │ session_id (FK)         │        │ session_id (FK)        │          │ session_id (FK)         │
 │ agent_name (TEXT)       │        │ tool_name (TEXT)       │          │ report_markdown (TEXT)  │
 │ message (TEXT)          │        │ status (TEXT)          │          │ report_json (JSONB)     │
 └─────────────────────────┘        │ execution_time (REAL)  │          │ pdf_url (TEXT)          │
                                    │ confidence (REAL)      │          │ docx_url (TEXT)         │
                                    │ cache_hit (BOOLEAN)    │          │ pptx_url (TEXT)         │
                                    │ source_count (INTEGER) │          │ html_url (TEXT)         │
                                    └────────────────────────┘          │ markdown_url (TEXT)     │
                                                                        └─────────────────────────┘
```

---

## 2. Table Specifications

### 2.1 Table: `research_sessions`
Tracks individual execution requests and caching states.
```sql
CREATE TABLE research_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL DEFAULT 'anon-user-uuid',
    company_name TEXT NOT NULL,
    domain TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('planned', 'running', 'completed', 'failed')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    version INTEGER NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_research_sessions_user ON research_sessions(user_id);
CREATE INDEX idx_research_sessions_status ON research_sessions(status);
```

### 2.2 Table: `research_execution_logs`
Saves execution progress events compiled per agent.
```sql
CREATE TABLE research_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exec_logs_session ON research_execution_logs(session_id);
```

### 2.3 Table: `tool_execution_logs`
Audits tool execution latency, confidence, source count, and caching hits.
```sql
CREATE TABLE tool_execution_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    tool_name TEXT NOT NULL,
    status TEXT NOT NULL,
    execution_time REAL NOT NULL,
    confidence REAL NOT NULL CHECK (confidence BETWEEN 0.0 AND 1.0),
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    source_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_logs_session ON tool_execution_logs(session_id);
```

### 2.4 Table: `research_reports`
Stores compiled research dossiers, markdown structures, and signed URL downloads.
```sql
CREATE TABLE research_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    report_markdown TEXT NOT NULL,
    report_json JSONB NOT NULL,
    pdf_url TEXT,
    docx_url TEXT,
    pptx_url TEXT,
    html_url TEXT,
    markdown_url TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_reports_session ON research_reports(session_id);
```

### 2.5 Table: `chat_messages`
Logs dialog history between user and follow-up assistant.
```sql
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES research_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    message TEXT NOT NULL,
    tool_used TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id);
```

### 2.6 Table: `content_drafts`
Caches synthesized LinkedIn, Twitter threads, emails, blogs, and newsletter drafts.
```sql
CREATE TABLE content_drafts (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    content_type TEXT NOT NULL,
    style TEXT NOT NULL,
    length TEXT NOT NULL,
    title TEXT,
    body TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    published BOOLEAN NOT NULL DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    published_platform TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_content_drafts_session ON content_drafts(session_id);
```

---

## 3. Storage Bucket Design

Create a private storage bucket named `reports` inside the Supabase Console.
- Access policies must permit authenticated select/insert operations.
- GravityAI resolves downloads using signed transient URLs valid for 1 hour to verify secure, authorized user downloads.
