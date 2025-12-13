# Building Zeffo: How We Engineered an AI-Powered Ticket Resolution Platform

*A deep dive into the architecture, technical decisions, and lessons learned from building a production-ready SaaS as CS students.*

---

## Introduction

Customer support teams are drowning. A mid-sized company might receive thousands of tickets monthly, many describing the same issue in different ways. Support agents spend hours writing repetitive responses, while customers wait frustrated.

We built **Zeffo** — an AI platform that clusters similar tickets, generates help articles from company documentation, and measures their real-world effectiveness through A/B testing.

This article walks through our engineering decisions, the trade-offs we faced, and what we learned shipping a production system.

**Team**: Juan Alonso-Allende, Luis Infante, Alejandro Helmrich, Caterina Barberos, Federica Caselli

---

## The Problem We're Solving

Support tickets are messy. Customers describe the same problem differently:
- *"Can't log in after password reset"*
- *"Reset password but still locked out"*
- *"Password change didn't work"*

These are the same issue — but they appear as three separate tickets. Agents write three separate responses. Knowledge bases bloat with near-duplicate articles.

**Zeffo's approach:**
1. **Cluster** tickets by underlying intent (not surface-level keywords)
2. **Generate** help articles using company documentation as ground truth
3. **Iterate** on content with human-in-the-loop feedback
4. **Measure** effectiveness via embedded A/B testing

---

## System Architecture

> **[DIAGRAM 1: High-Level Architecture]**
>
> Create a diagram showing:
> - **Left side**: Data sources (CSV uploads, future Zendesk API)
> - **Center**: Zeffo Platform with three layers:
>   - API Gateway (Nginx)
>   - Backend Services (FastAPI)
>   - Data Layer (MySQL, Redis, ChromaDB)
> - **Right side**: Outputs (Dashboard, Slack notifications, Embeddable Widget)
> - **Bottom**: Infrastructure (AWS EC2, S3, RDS)
>
> *Suggested tool: draw.io or Excalidraw*

### Why This Stack?

**Backend → FastAPI (Python)**
Async-first, native Pydantic validation, excellent for ML workloads.

**Database → MySQL + Alembic**
Battle-tested RDBMS with schema migrations for evolving data models.

**Vector Store → ChromaDB**
Lightweight, easy to self-host, sufficient for our scale.

**Cache & Queue Broker → Redis**
Sub-millisecond latency. Also powers our job queue via RQ.

**Task Queue → RQ (Redis Queue)**
Simple, Python-native, built-in retry mechanisms.

**Frontend → React + Vite + TypeScript**
Fast developer experience, type safety, component reusability.

**Auth → Firebase Authentication**
Managed auth with social logins and JWT tokens out of the box.

**Infrastructure as Code → Terraform**
Multi-cloud support — we target both AWS and Azure.

**Config Management → Ansible**
Idempotent server configuration, easy Docker orchestration.

---

## Deep Dive: The AI Pipeline

The core of Zeffo is a multi-stage pipeline that transforms raw tickets into actionable help articles.

> **[DIAGRAM 2: Ticket Processing Pipeline]**
>
> Create a flowchart showing:
> 1. **CSV Upload** → 2. **Batch Processing (RQ Workers)** → 3. **LLM Clustering** → 4. **Intent Assignment** → 5. **RAG Article Generation** → 6. **Human Review** → 7. **Export**
>
> Show the feedback loop from step 6 back to step 5.
>
> *Suggested tool: Excalidraw with arrows*

### Stage 1: Intelligent Clustering

We don't cluster by keywords — we cluster by **intent**. The same customer frustration expressed in ten different ways should map to one intent.

**The challenge**: Existing intents might already cover a new ticket's issue. We need the LLM to either:
- **Match** to an existing intent, or
- **Create** a new one with proper categorization

```python
# Simplified clustering logic
async def cluster_tickets(tickets: List[Dict]) -> Dict:
    # Fetch existing intents with 3-tier category hierarchy
    existing_intents = await get_all_intents_with_categories(db)

    # Single LLM call for entire batch (cost optimization)
    prompt = build_batch_clustering_prompt(tickets, existing_intents)
    llm_result = await llm_client.call_structured(prompt, schema)

    # Process decisions: MATCH existing or CREATE new
    for assignment in llm_result["assignments"]:
        if assignment["decision"] == "match_existing":
            await assign_to_intent(ticket, assignment["intent_id"])
        else:
            await create_intent_with_category_hierarchy(ticket, assignment)
```

**Key decisions:**
- **Batched LLM calls**: Processing tickets individually would be prohibitively expensive. We batch tickets and make one structured LLM call.
- **Caching by content hash**: Identical ticket batches return cached results (SHA256 hash of sorted ticket texts).
- **3-tier category hierarchy**: Intents belong to L3 categories, which belong to L2, which belong to L1. This enables organized knowledge bases.

### Stage 2: RAG-Based Article Generation

We use a **LangGraph** workflow for article generation. The key insight: company documentation is the source of truth, not the LLM's general knowledge.

> **[DIAGRAM 3: RAG Workflow]**
>
> Create a simple two-node flowchart:
> 1. **Retrieve**: Query ChromaDB with intent + ticket summaries → Get top-k relevant doc chunks
> 2. **Generate**: Feed context + tickets to Gemini → Output structured article (title, summary, content)
>
> *Suggested tool: Simple boxes with arrows*

```python
class RAGWorkflow:
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(RAGState)

        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("generate_article", self._generate_article)

        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate_article")
        workflow.add_edge("generate_article", END)

        return workflow.compile()
```

**Human-in-the-loop iteration**: Articles aren't auto-published. SMEs review, provide feedback, and trigger regeneration. The workflow tracks iteration count and incorporates feedback into subsequent generations.

---

## Infrastructure: From Dev to Production

We invested heavily in infrastructure automation. A single `git tag` triggers a full production deployment.

> **[DIAGRAM 4: CI/CD Pipeline]**
>
> Create a horizontal pipeline:
> 1. **Push tag (v*.*.*)** → 2. **Detect changes (infra vs app)** → 3. **Terraform Apply** → 4. **Docker Build & Push** → 5. **Ansible Playbook** → 6. **Health Checks**
>
> Show conditional paths: "Infra changed?" and "App changed?"
>
> *Suggested tool: draw.io with decision diamonds*

### Multi-Cloud Terraform

We maintain Terraform modules for both AWS and Azure. Same architecture, different providers.

```
infra/terraform/
├── aws/
│   ├── modules/
│   │   ├── ec2/
│   │   ├── rds/
│   │   ├── s3/
│   │   └── vpc/
│   └── environment/
│       ├── dev/
│       ├── staging/
│       └── production/
└── azure/
    ├── modules/
    │   ├── vm/
    │   ├── mysql_db/
    │   ├── blob_storage/
    │   └── network/
    └── environment/
        └── production/
```

**Why multi-cloud?** Enterprise customers have cloud preferences. Supporting both from day one means we don't have to rewrite infrastructure later.

### Queue Architecture

Background jobs are critical for our async pipeline. We use RQ with a multi-stage architecture:

```python
# Stage 1: Cluster batch of tickets
def process_ticket_stage1(ticket_batch: List[Dict]) -> List[Dict]:
    filtered_tickets = [save_tickets(t) for t in ticket_batch]
    clustered_tickets = cluster_ticket(filtered_tickets)
    return clustered_tickets

# Stage 2: Generate content (one per unique cluster)
def process_ticket_stage2(ticket_data: Dict) -> Dict:
    return generate_content(ticket_data)

# Finalizer: Orchestrate stage transitions
def batch_finalizer(stage1_job_ids: List[str]) -> Dict:
    # Wait for stage 1 completion
    # Deduplicate by cluster
    # Enqueue stage 2 only for clusters needing articles
```

**Key insight**: Not every ticket needs a new article. If 50 tickets cluster into 3 intents, and 2 intents already have approved articles, we only generate 1 new article.

---

## The A/B Testing Widget

The most underrated feature: **measuring what works**.

When SMEs export an approved article, they get an embeddable React component. This component:
1. Tracks **impressions** (article was shown)
2. Tracks **resolutions** (user didn't open a ticket within 10 minutes)
3. Tracks **ticket creation** (user still needed human help)

```javascript
// Simplified ingest.js
function init() {
    intentId = getIntentId();
    variant = getVariant(intentId);  // A/B assignment persisted in localStorage

    // Immediate impression
    sendEvent("impression", { intent_id: intentId, variant });

    // Scheduled resolution (cancelled if ticket created)
    resolutionTimeout = setTimeout(() => {
        sendEvent("resolution", { intent_id: intentId, variant });
    }, 10 * 60 * 1000);
}

// Customer calls this when user opens ticket form
window.SupportAI.ticketCreated = function() {
    clearTimeout(resolutionTimeout);
    sendEvent("ticket_created", { intent_id: intentId, variant });
};
```

This gives SMEs data: "Article v2 resolved 73% of users vs 61% for v1." Content decisions become evidence-based.

---

## Business Relevance

Why does this matter beyond the engineering?

**For Support Teams:**
- Reduce time-to-resolution by surfacing relevant articles proactively
- Decrease ticket volume by helping customers self-serve
- Maintain consistency across support responses

**For Product Teams:**
- Identify recurring pain points through cluster analysis
- Prioritize fixes based on ticket volume per intent
- Measure the impact of help content on support load

**For Engineering Teams:**
- Integrate via simple widget — no backend changes required
- API-first design enables custom integrations
- Self-hostable for data-sensitive customers

---

## Lessons Learned

### 1. Batch Everything
Early prototypes made one LLM call per ticket. At scale, this was slow and expensive. Batching tickets into single structured calls reduced costs by ~80% and improved latency.

### 2. Cache Aggressively, Invalidate Carefully
We cache clustering results, document embeddings, and article generations. The tricky part: knowing when to invalidate. Content hashes (not timestamps) give us deterministic cache keys.

### 3. Human-in-the-Loop is Non-Negotiable
Fully automated article publishing sounds efficient — until an LLM hallucinates policy details. The review step adds latency but prevents costly mistakes.

### 4. Infrastructure is a Feature
We spent significant time on Terraform, Ansible, and CI/CD. This paid off immediately: deployments are one-click, rollbacks are trivial, and onboarding new environments takes hours, not days.

### 5. Start with Observability
Prometheus + Grafana from day one. When something breaks in production, you need metrics and logs — not `print()` statements and guesswork.

---

## What's Next

- **Direct Zendesk/Intercom integration**: Replace CSV uploads with real-time ticket sync
- **Multi-language support**: Cluster and generate articles in the customer's language
- **Suggested responses**: Real-time article suggestions for agents mid-conversation
- **Advanced analytics**: Cohort analysis, trend detection, seasonal patterns

---

## Conclusion

Building Zeffo taught us that production systems are 20% algorithms and 80% everything else: infrastructure, observability, user experience, and operational resilience.

The AI components (clustering, RAG, generation) are important — but they're table stakes. The differentiation comes from the full system: seamless deployment, human-in-the-loop workflows, and measurable outcomes.

If you're a CS student building side projects: invest in infrastructure. Learn Terraform. Understand CI/CD. These skills compound, and they're what separate demos from products.

---

*Questions or feedback? Reach out on LinkedIn.*

---

**Tags**: #SaaS #AI #MachineLearning #RAG #Terraform #AWS #Startup #SoftwareEngineering #CustomerSupport
