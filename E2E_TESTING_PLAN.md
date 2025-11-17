# E2E Testing & Mock Data - Comprehensive Plan

**Status:** KANBAN 1 COMPLETE ✅ | WAITING FOR DEPENDENCIES FOR KANBAN 2 & 3

**Current Progress:**
- ✅ **Kanban 1 (Integration Tests):** FULLY DONE - 17/17 tests passing
- ⏳ **Kanban 2 (E2E Plan + Fixtures):** BLOCKED - waiting for @catebros & @LAIN-21
- ⏳ **Kanban 3 (Automated Full Pipeline):** BLOCKED - waiting for real implementations

**What's Completed:**
- ✅ Integration test infrastructure (conftest.py, fixtures)
- ✅ CSV → Draft pipeline tests (4 tests)
- ✅ Approval flow tests (4 tests)
- ✅ Publishing flow tests (6 tests)
- ✅ Widget rendering tests (3 tests)
- ✅ Markdown-to-HTML conversion implemented
- ✅ Slack integration endpoints (mocked for tests)
- ✅ Clustering endpoint integration (mocked for tests)

**What's Waiting:**
- ❌ @catebros: LLMClient, cluster_and_categorize_tickets(), draft generation, publishing
- ❌ @LAIN-21: Real Slack API integration (currently stubbed)

---

## TASK 1: E2E Test Plan Documentation

### What Needs to Be Documented

#### 1.1 Main User Flows

**Flow 1: Happy Path (All Steps Work)**
```
1. User logs in (Auth)
2. User navigates to dashboard
3. User uploads CSV file
4. System clusters/categorizes tickets
5. AI generates draft content for tickets
6. User reviews draft in dashboard/Slack
7. User approves or requests edits
8. If approved: System publishes to microsite
9. Widget becomes visible on user's website
10. Widget fetches and displays micro-answer
```

**Flow 2: Rejection Path (Needs Edits)**
```
1-6. Same as happy path
7. User requests edits on draft
8. Draft status → NEEDS_EDIT
9. System notifies user (via Slack/dashboard)
10. User can re-upload or edit manually
11. User resubmits for approval
12. Continue with approval process
```

#### 1.2 Data Paths to Document

**Path 1: CSV Ingestion**
```
User File Upload
  ↓
/api/csv/upload endpoint
  ↓
CSV Parser (validate format, fields)
  ↓
Create Ticket records in database
  ↓
Ticket status: UPLOADED
  ↓
Ready for clustering
```

**Path 2: Clustering**
```
Ticket (UPLOADED)
  ↓
/api/tickets/{id}/cluster endpoint
  ↓
Clustering algorithm (ML model or service)
  ↓
Group tickets into categories
  ↓
Ticket status: PROCESSING
  ↓
Ready for drafting
```

**Path 3: Draft Generation**
```
Clustered Ticket (PROCESSING)
  ↓
/api/drafts/generate endpoint
  ↓
AI Content Generation (LLM integration)
  ↓
Generate markdown draft content
  ↓
Create Draft record in database
  ↓
Draft status: PENDING
  ↓
Ready for approval
```

**Path 4: Approval Flow**
```
Draft (PENDING)
  ↓
/api/drafts/{id}/send-for-approval endpoint
  ↓
Create Approval record
  ↓
Send notification (Slack, email, dashboard)
  ↓
Approval status: PENDING
  ↓
User responds (approved/needs_edit)
  ↓
/api/approvals/{id}/handle-response endpoint
  ↓
Update Draft status (APPROVED or NEEDS_EDIT)
  ↓
Update Approval status
```

**Path 5: Publishing**
```
Draft (APPROVED)
  ↓
/api/articles/publish/{draft_id} endpoint
  ↓
Markdown Microsite Generator
  ↓
Generate HTML/microsite URL
  ↓
Create PublishedArticle record
  ↓
Draft status: PUBLISHED
  ↓
Article visible on microsite
```

**Path 6: Widget Rendering**
```
Published Article
  ↓
User's website (embedded widget)
  ↓
Widget calls /api/widget/render/{article_id}
  ↓
Returns HTML with micro-answer
  ↓
Widget displays content in user's site
```

#### 1.3 Data State Transitions

**Ticket States:**
```
UPLOADED → PROCESSING → DRAFT_READY
```

**Draft States:**
```
PENDING → AWAITING_APPROVAL → APPROVED → PUBLISHED
         ↓
      NEEDS_EDIT (loops back)
```

**Approval States:**
```
PENDING → APPROVED
        → NEEDS_EDIT
```

**PublishedArticle States:**
```
CREATED (when draft published)
```

---

## COMPLETED: Integration Tests (Kanban 1)

### Test Files
- ✅ `backend/tests/integration/test_csv_draft_pipeline.py` - 4 tests
- ✅ `backend/tests/integration/test_approval_flow.py` - 4 tests
- ✅ `backend/tests/integration/test_publish_flow.py` - 6 tests
- ✅ `backend/tests/integration/test_js_widget.py` - 3 tests

### Stub Files Created (Awaiting Implementation)
- `backend/src/ai_ticket_platform/core/clients/llm.py` - LLMClient stub (pending @catebros)
- `backend/src/ai_ticket_platform/core/clients/slack.py` - Slack stub (pending @LAIN-21)
- `backend/src/ai_ticket_platform/services/clustering/cluster_service.py` - clustering stub (pending @catebros)

### Implementations Done
- ✅ Markdown-to-HTML conversion in widget endpoint
- ✅ Slack integration calls in approval endpoints (mocked for tests)
- ✅ Clustering service calls in CSV endpoint (mocked for tests)
- ✅ All database state transitions tested

---

## BLOCKING ISSUES FOR KANBAN 2 & 3

### From @catebros (Backend + Business Logic)

**1. LLMClient Implementation** (`backend/src/ai_ticket_platform/core/clients/llm.py`)
- Current: Stub with NotImplementedError
- Needed: Implement `call(prompt: str, **kwargs) -> str` method
- Purpose: Used by cluster_and_categorize_tickets()

**2. Clustering Service** (`backend/src/ai_ticket_platform/services/clustering/cluster_service.py`)
- Current: Stub with NotImplementedError
- Needed: Implement `cluster_and_categorize_tickets(tickets, llm_client)`
- Expected Return:
  ```python
  {
    'total_tickets': int,
    'clusters_created': int,
    'clusters': [
      {'topic_name': str, 'product_category': str, 'tickets_count': int},
      ...
    ]
  }
  ```

**3. Draft Generation** (`backend/src/ai_ticket_platform/routers/drafts.py`)
- Current: Mock content at line 65-78
- Needed: Real AI draft generation using LLM
- Location: `/api/drafts/generate` endpoint

**4. Publishing/Microsite Generator** (`backend/src/ai_ticket_platform/routers/publishing.py`)
- Current: Mock URL generation
- Needed: Real markdown microsite generator
- Location: `/api/articles/publish/{draft_id}` endpoint

### From @LAIN-21 (Frontend + Slack)

**1. Slack Integration** (`backend/src/ai_ticket_platform/core/clients/slack.py`)
- Current: Stub with NotImplementedError
- Needed: Implement 2 methods:
  - `send_new_article_proposal(slack_channel_id, url, content)` → returns `(thread_ts, message_ts)`
  - `send_confirmation_message(slack_channel_id, url)` → returns message_ts
- Used by: `/api/drafts/{draft_id}/send-for-approval` and `/api/approvals/{approval_id}/handle-response`

---

## What to Do When Dependencies Are Ready

1. **Merge @catebros branch** - integrate LLM, clustering, drafting, publishing
2. **Merge @LAIN-21 branch** - integrate Slack API
3. **Remove test mocks** - replace `patch()` calls with real implementations
4. **Run tests again** - verify all 17 tests still pass with real code
5. **Create Kanban 2 fixtures** - build sample CSV data
6. **Create Kanban 3 E2E test** - full CSV → widget pipeline test

---

## File Structure When Ready

```
backend/
├── tests/
│   ├── e2e/
│   │   └── test_full_pipeline.py (to create)
│   ├── fixtures/
│   │   ├── tickets_sample.csv (to create - 100 entries)
│   │   ├── tickets_edge_cases.csv (to create)
│   │   ├── sample_markdown_outputs/
│   │   │   ├── clustering_groups.md (to create)
│   │   │   ├── draft_example.md (to create)
│   │   │   └── published_article_example.md (to create)
│   │   └── README.md (to create)
│   └── integration/
│   │   ├── test_csv_draft_pipeline.py ✅ (DONE)
│   │   ├── test_approval_flow.py ✅ (DONE)
│   │   ├── test_publish_flow.py ✅ (DONE)
│   │   ├── test_js_widget.py ✅ (DONE)
│   │   └── conftest.py ✅ (DONE)
├── API_CONTRACTS.md (to create)
└── E2E_TESTING_PLAN.md (this file)
```

---

## Timeline

| Phase | Status | What |
|-------|--------|------|
| **Phase 0** | ✅ DONE | Setup test infrastructure |
| **Phase 1** | ✅ DONE | Create integration tests (17 tests) |
| **Phase 2** | ⏳ BLOCKED | Waiting for @catebros clustering + @LAIN-21 Slack |
| **Phase 3** | ⏳ BLOCKED | Create mock data fixtures (100 CSV entries) |
| **Phase 4** | ⏳ BLOCKED | Create full E2E automated test |
| **Phase 5** | ⏳ BLOCKED | Verify end-to-end CSV → widget pipeline |

---

## Notes

- **All integration tests are runnable** via `make test-integration`
- **Tests use mocks** to avoid external dependencies during development
- **Infrastructure is ready** for real implementations once teammates finish
- **No E2E/fixture tests yet** - blocked on teammate implementations

---

**Last Updated:** 2025-11-17 (Integration tests complete)
**Status:** KANBAN 1 DONE | WAITING FOR TEAMMATES
**Next Step:** Check status with @catebros and @LAIN-21, then proceed with Kanban 2 & 3
