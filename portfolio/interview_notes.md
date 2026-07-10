# Interview Preparation Notes - GravityAI Design Decisions

These notes summarize the architectural trade-offs, challenging engineering problems, and scaling design decisions of GravityAI for technical interviews.

---

## 1. Why LangGraph for Multi-Agent Orchestration?

**Alternative Considered:** Standard sequential loops, LangChain chains, or autogen swarm models.
**Trade-Off Decision:**
- **Autogen / Swarms** are highly conversational but unpredictable and prone to "infinite loops" or diverging execution paths.
- **Sequential chains** are too rigid; they cannot handle dynamic specialist routing or self-correction feedback loops.
- **LangGraph** provides a deterministic state-machine wrapper over LLM calls. It allows defining strict validation edges, cycle safety limits (e.g., maximum 3 reviewer loops), parallel node processing, and persistent state management.

---

## 2. Engineering Factual Integrity with the Evidence Store

**The Challenge:** LLMs are notorious for hallucinating financial figures and dates.
**The Solution:**
- Every specialist scraper (financial tool, tech stack tool, hiring crawler) returns structured Pydantic models.
- Every factual object (`FactualString`, `FactualInt`, `FactualList`) *must* reference one or more `Evidence` models containing:
  - `quote`: Verbatim text snippet extracted from source.
  - `source`: The origin name.
  - `url`: Direct source link.
  - `confidence`: Calculated tool confidence.
- The **Report Reviewer Agent** acts as an automated QA gate. It reviews the compiled state. If it finds sections with zero evidence, default values, or outright contradictions (e.g. profile is for Stripe but valuation lists Microsoft), it flags the affected specialist for re-execution.

---

## 3. Modular Document Compilation vs. Dynamic Rendering

**The Challenge:** Users expect publication-ready PDF, Word, and PowerPoint assets matching strict brand guidelines, generated instantly without heavy cloud dependencies.
**The Solution:**
- Extracted visualization logic into a standalone `chart_generator.py` using **Matplotlib** to write custom, reusable `ChartDefinition` payloads.
- Structured document-compilation pipelines using native libraries (**ReportLab** for PDF flowables, **python-docx**, and **python-pptx**) running locally inside the API containers.
- Compiled final multi-format assets under 4 seconds, uploading to Supabase Storage, and serving signed transient URLs to prevent unauthorized access.
