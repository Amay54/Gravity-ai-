# API Reference - GravityAI

This document describes the API routes exposed by the GravityAI FastAPI backend gateway. All endpoints are prefixed with `/api/v1`.

## 1. System Endpoints

### 1.1 Health Check
* **Endpoint**: `GET /api/v1/system/health`
* **Description**: Verifies if the backend API is online.
* **Response (200 OK)**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2026-07-09T15:00:00Z"
  }
  ```

### 1.2 System Version
* **Endpoint**: `GET /api/v1/system/version`
* **Description**: Returns version and build metadata.
* **Response (200 OK)**:
  ```json
  {
    "version": "0.1.0",
    "environment": "development"
  }
  ```

### 1.3 System Status
* **Endpoint**: `GET /api/v1/system/status`
* **Description**: Checks active connections to external microservices (Supabase API, Gemini API connection checks).
* **Response (200 OK)**:
  ```json
  {
    "status": "operational",
    "services": {
      "supabase": "connected",
      "gemini_api": "connected"
    }
  }
  ```

---

## 2. Research Endpoints

### 2.1 Trigger Research
* **Endpoint**: `POST /api/v1/research`
* **Description**: Submits a new target company for agent investigation. This is non-blocking and executes in the background.
* **Request Payload**:
  ```json
  {
    "company_name": "Stripe",
    "domain": "stripe.com",
    "depth": "comprehensive"
  }
  ```
* **Response (202 Accepted)**:
  ```json
  {
    "job_id": "8f2b3112-70b9-4aeb-98ff-cf0c39f046c8",
    "status": "pending",
    "message": "Research job submitted successfully."
  }
  ```

### 2.2 Get Research Status
* **Endpoint**: `GET /api/v1/research/{job_id}/status`
* **Description**: Retrieves real-time execution steps, currently running agents, and log progress.
* **Response (200 OK)**:
  ```json
  {
    "job_id": "8f2b3112-70b9-4aeb-98ff-cf0c39f046c8",
    "status": "running",
    "running_agents": ["ResearchAgent", "FinanceAgent"],
    "completed_agents": ["PlannerAgent"],
    "logs": [
      {
        "timestamp": "2026-07-09T15:01:02Z",
        "agent": "PlannerAgent",
        "message": "Planning completed. Starting Research and Finance investigation."
      }
    ]
  }
  ```

### 2.3 Fetch Report Result
* **Endpoint**: `GET /api/v1/research/{job_id}/report`
* **Description**: Returns the compiled company report in Markdown format.
* **Response (200 OK)**:
  ```json
  {
    "job_id": "8f2b3112-70b9-4aeb-98ff-cf0c39f046c8",
    "company_name": "Stripe",
    "report_markdown": "# Stripe Research Report ...",
    "created_at": "2026-07-09T15:05:00Z"
  }
  ```

### 2.4 Download Report PDF
* **Endpoint**: `GET /api/v1/research/{job_id}/download`
* **Description**: Downloads the final compiled PDF report file.
* **Response**: Binary stream file (`application/pdf`).

### 2.5 Generate LinkedIn Post
* **Endpoint**: `POST /api/v1/research/{job_id}/linkedin`
* **Description**: Summarizes the research outcomes into a copy-pasteable social post.
* **Response (200 OK)**:
  ```json
  {
    "job_id": "8f2b3112-70b9-4aeb-98ff-cf0c39f046c8",
    "linkedin_post": "🚀 Stripe's next move: a deep-dive analysis of..."
  }
  ```

---

## 3. Swagger/OpenAPI Documentation
FastAPI automatically registers OpenAPI schemas. You can visually inspect and test these endpoints using:
* **Swagger UI**: `/docs`
* **Redoc UI**: `/redoc`
