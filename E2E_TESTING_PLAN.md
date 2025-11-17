# E2E Testing & Mock Data - Comprehensive Plan

**Status:** KANBAN 1 & 2 COMPLETE ✅ | KANBAN 3 BLOCKED ON TEAMMATES

**Current Progress:**
- ✅ **Kanban 1 (Integration Tests):** FULLY DONE - 17 tests passing
- ✅ **Kanban 2 (E2E Plan + Fixtures):** FULLY DONE - 8 tests passing + fixtures created
- ⏳ **Kanban 3 (Automated Full Pipeline):** BLOCKED - waiting for real implementations from @catebros & @LAIN-21

**What's Completed (Kanban 1 & 2):**
- ✅ Integration test infrastructure (conftest.py with TestSettings)
- ✅ CSV → Draft pipeline tests (4 tests in test_csv_draft_pipeline.py)
- ✅ Complete CSV flow tests (8 tests in test_csv_complete_flow.py)
- ✅ Approval flow tests (4 tests in test_approval_flow.py)
- ✅ Publishing flow tests (6 tests in test_publish_flow.py)
- ✅ Widget rendering tests (3 tests in test_js_widget.py)
- ✅ Mock data fixtures (tickets_sample.csv with 84 entries, edge_cases.csv with 40+ entries)
- ✅ Sample markdown outputs (draft, clustering, published article examples)
- ✅ Comprehensive fixture documentation (README.md)
- ✅ Markdown-to-HTML conversion implemented and working
- ✅ Slack integration endpoints (mocked for tests)
- ✅ Clustering endpoint integration (mocked for tests)

**What's Blocked on Teammates (Kanban 3):**
- ❌ @catebros: LLMClient.call(), cluster_and_categorize_tickets(), real draft generation, microsite generator
- ❌ @LAIN-21: Slack API send_new_article_proposal(), send_confirmation_message(), widget frontend

---

## KEY FINDING: KANBAN INDEPENDENCE

### Kanban 1 & 2: INDEPENDENT ✅
**Neither Kanban 1 nor Kanban 2 depend on @catebros or @LAIN-21 implementations.**

- All integration tests use `unittest.mock.patch()` to mock external services
- Mock data fixtures are self-contained and don't require real AI/Slack APIs
- Tests pass successfully with stubbed implementations
- Documentation is complete and ready for review

**Result:** Both kanbans are FULLY COMPLETE and READY FOR PRODUCTION

### Kanban 3: FULLY BLOCKED ⏳
**Kanban 3 (Automated Full Pipeline) cannot proceed without real implementations from both teammates.**

- Tests will fail if we try to run without real implementations
- Blocking on 2 separate implementations from 2 different teammates
- Cannot proceed in parallel - both are critical path

---

## BLOCKING ANALYSIS FOR KANBAN 3

### From @catebros (Backend/AI Integration)

| Component | Location | Status | What's Needed | Impact |
|-----------|----------|--------|---------------|--------|
| **LLMClient** | `backend/src/ai_ticket_platform/core/clients/llm.py:21-23` | ❌ NotImplementedError | Implement `call(prompt, **kwargs) -> str` method | CRITICAL - Used by clustering service |
| **Clustering Service** | `backend/src/ai_ticket_platform/services/clustering/cluster_service.py:23` | ❌ NotImplementedError | Implement `cluster_and_categorize_tickets(tickets, llm_client)` function | CRITICAL - CSV upload endpoint depends on this |
| **Draft Generation** | `backend/src/ai_ticket_platform/routers/drafts.py:63` | ⚠️ Mock Content | Replace mock content with real LLM call to generate drafts | HIGH - Currently returns hardcoded template |
| **Microsite Generator** | `backend/src/ai_ticket_platform/routers/publishing.py:82` | ⚠️ Mock URL | Implement actual markdown→HTML microsite generator | HIGH - Currently returns UUID-based mock URLs |
| **Widget Rendering** | `backend/src/ai_ticket_platform/routers/widget.py:35` | ✅ Implemented | Markdown-to-HTML conversion working (uses markdown library) | COMPLETE |

### From @LAIN-21 (Frontend/Slack Integration)

| Component | Location | Status | What's Needed | Impact |
|-----------|----------|--------|---------------|--------|
| **send_new_article_proposal()** | `backend/src/ai_ticket_platform/core/clients/slack.py:37` | ❌ NotImplementedError | Implement Slack API call to send draft proposal message | CRITICAL - Approval workflow depends on this |
| **send_confirmation_message()** | `backend/src/ai_ticket_platform/core/clients/slack.py:57` | ❌ NotImplementedError | Implement Slack API call to send confirmation message | CRITICAL - Publishing confirmation depends on this |
| **Widget Frontend** | `frontend/` | ⚠️ Pending | Build JS widget for embedding on user websites | HIGH - Consumer-facing component |

### Expected Return Formats (for @catebros)

**cluster_and_categorize_tickets() must return:**
```python
{
  'total_tickets': int,
  'clusters_created': int,
  'clusters': [
    {
      'topic_name': str,          # e.g., "Authentication"
      'product_category': str,     # e.g., "Security"
      'confidence_score': float,   # 0.0-1.0
      'tickets_count': int
    },
    ...
  ]
}
```

**LLMClient.call() signature:**
```python
def call(self, prompt: str, **kwargs) -> str:
    """Make LLM call and return text response"""
    # Implementation here
```

**send_new_article_proposal() must return:**
```python
# Returns tuple of (thread_ts, message_ts) from Slack
# Example: ("1234567890.123456", "1234567890.654321")
```

**send_confirmation_message() must return:**
```python
# Returns message_ts from Slack
# Example: "1234567890.654321"
```

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

## DETAILED BLOCKERS FOR KANBAN 3

This section contains exact blocking points that prevent Kanban 3 from running. All blocking items prevent the full end-to-end pipeline from working with real data.

---

## Integration Path for Kanban 3

When @catebros and @LAIN-21 complete their implementations:

1. **Merge @catebros branch**
   - Replaces NotImplementedError in llm.py with real LLM API calls
   - Replaces NotImplementedError in cluster_service.py with real clustering algorithm
   - Replaces mock content in drafts.py with LLM-generated content
   - Replaces mock URL generation in publishing.py with real microsite generator

2. **Merge @LAIN-21 branch**
   - Replaces NotImplementedError in slack.py with real Slack API calls
   - Implements send_new_article_proposal() to send draft to Slack
   - Implements send_confirmation_message() to send publish notification

3. **Remove test mocks**
   - Replace `patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets')` in tests
   - Replace `patch('ai_ticket_platform.core.clients.slack')` in tests
   - Tests will now use real implementations instead of mocks

4. **Run full integration suite**
   - All 25 tests should still pass (17 Kanban 1 + 8 Kanban 2)
   - Add Kanban 3 end-to-end test: CSV → Clustering → Draft → Approval → Publish → Widget

5. **Create Kanban 3 test fixtures**
   - tickets_sample.csv is ready (already created in Kanban 2)
   - Create sample_markdown_outputs with real AI-generated examples

6. **Validate end-to-end flow**
   - User uploads CSV
   - System clusters tickets (real AI)
   - System generates drafts (real AI)
   - Approval sent via Slack (real API)
   - Article published to microsite (real generator)
   - Widget renders on user's site

---

## File Structure (Current State)

```
backend/
├── tests/
│   ├── fixtures/
│   │   ├── tickets_sample.csv ✅ (84 sample tickets)
│   │   ├── tickets_edge_cases.csv ✅ (40+ edge case entries)
│   │   ├── sample_markdown_outputs/
│   │   │   ├── clustering_groups.md ✅ (9-cluster example)
│   │   │   ├── draft_example.md ✅ (AI draft template)
│   │   │   └── published_article_example.md ✅ (Published article example)
│   │   └── README.md ✅ (Fixture documentation)
│   └── integration/
│   │   ├── test_csv_draft_pipeline.py ✅ (4 tests)
│   │   ├── test_csv_complete_flow.py ✅ (8 tests)
│   │   ├── test_approval_flow.py ✅ (4 tests)
│   │   ├── test_publish_flow.py ✅ (6 tests)
│   │   ├── test_js_widget.py ✅ (3 tests)
│   │   └── conftest.py ✅ (Test infrastructure)
├── src/ai_ticket_platform/
│   ├── core/clients/
│   │   ├── llm.py ⏳ (Awaiting @catebros)
│   │   └── slack.py ⏳ (Awaiting @LAIN-21)
│   ├── services/clustering/
│   │   └── cluster_service.py ⏳ (Awaiting @catebros)
│   └── routers/
│       ├── drafts.py (Mock content, awaiting @catebros real AI)
│       ├── publishing.py (Mock URLs, awaiting @catebros microsite generator)
│       └── widget.py ✅ (Markdown-to-HTML conversion working)
└── E2E_TESTING_PLAN.md ✅ (This file)

frontend/
└── widget/ ⏳ (Awaiting @LAIN-21 implementation)
```

**Summary:**
- **25 tests** passing (17 Kanban 1 + 8 Kanban 2)
- **6 fixture files** created (CSV + markdown examples)
- **5 integration test files** implemented
- **0 dependencies** on teammates needed for Kanban 1 & 2

---

## Timeline

| Phase | Status | Completion Date |
|-------|--------|-----------------|
| **Phase 0** | ✅ DONE | 2025-11-15 - Setup test infrastructure |
| **Phase 1** | ✅ DONE | 2025-11-16 - Create integration tests (17 tests) |
| **Phase 2** | ✅ DONE | 2025-11-17 - Create mock data fixtures & Kanban 2 tests (8 tests) |
| **Phase 3** | ⏳ BLOCKED | Waiting for @catebros LLMClient implementation |
| **Phase 4** | ⏳ BLOCKED | Waiting for @LAIN-21 Slack API implementation |
| **Phase 5** | ⏳ BLOCKED | Create full E2E automated test with real implementations |
| **Phase 6** | ⏳ BLOCKED | Verify end-to-end CSV → widget pipeline |

---

## Quick Reference

### How to Run Tests
```bash
cd backend
make test-integration          # Run all 25 tests
make test-integration-csv      # Run CSV pipeline tests only
make test-integration-approval # Run approval flow tests only
make test-integration-publish  # Run publishing tests only
make test-integration-widget   # Run widget tests only
```

### What Works Right Now
- ✅ CSV upload and parsing
- ✅ Ticket creation from CSV data
- ✅ Draft creation (with mock content)
- ✅ Approval workflow (with mocked Slack)
- ✅ Article publishing (with mock URLs)
- ✅ Widget rendering (Markdown → HTML conversion)
- ✅ All database state transitions
- ✅ All 25 integration tests passing

### What Requires Teammates
- ❌ Real LLM API integration (clustering, drafting)
- ❌ Real Slack API calls (approval notifications)
- ❌ Real microsite generator
- ❌ Widget frontend implementation

### Test Infrastructure
- Uses `pytest` with `pytest-asyncio` for async test support
- AsyncSession for database testing
- TestSettings dependency injection for isolated tests
- Mocks with `unittest.mock.patch()` for external services
- Fixtures for reusable test data

---

**Last Updated:** 2025-11-17 (Kanban 2 complete with blockers analysis)
**Status:** KANBAN 1 & 2 COMPLETE ✅ | KANBAN 3 BLOCKED ON TEAMMATES
**Next Steps:**
1. Get approval from @catebros for implementation specs
2. Get approval from @LAIN-21 for implementation specs
3. Integrate merged branches when available
4. Re-run tests with real implementations
