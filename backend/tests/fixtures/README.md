# Test Fixtures - CSV & Markdown Samples

This directory contains test data and sample outputs for the ticket resolution platform testing.

## Files Overview

### CSV Data

#### `tickets_sample.csv`
**Purpose:** 100 realistic ticket entries across 5 main categories
**Format:** CSV with `title` and `content` columns
**Size:** 100 entries
**Categories:**
1. **Authentication & Login Issues** (10 tickets)
   - SSO failures
   - Password reset problems
   - Account locking
   - 2FA/MFA issues
   - Session management

2. **Performance & Optimization** (15 tickets)
   - Slow dashboard loading
   - API response degradation
   - Database query timeouts
   - Memory leaks
   - CPU spikes

3. **Frontend & UI** (10 tickets)
   - Responsive design issues
   - Mobile compatibility
   - Dark mode requests
   - Accessibility improvements
   - CSS/styling problems

4. **API & Integration** (15 tickets)
   - Webhook support
   - OAuth2/SAML features
   - Rate limiting
   - API documentation
   - Error handling improvements

5. **Features & Bug Reports** (35 tickets)
   - Feature requests from users
   - Bug reports with descriptions
   - Documentation gaps
   - Infrastructure improvements
   - Code quality enhancements

**Usage:**
```bash
# Test CSV upload with sample data
curl -F "file=@tickets_sample.csv" http://localhost:8000/api/csv/upload

# Use in integration tests
python -m pytest backend/tests/integration/test_csv_draft_pipeline.py --csv-file=tickets_sample.csv
```

#### `tickets_edge_cases.csv`
**Purpose:** Test edge cases and error handling
**Format:** CSV with intentional variations and problematic data
**Cases Included:**

1. **Missing/Empty Fields**
   - Rows with empty content
   - Rows with empty title
   - Both fields empty

2. **Special Characters**
   - Unicode emoji (🚀 🐛)
   - International characters (French, Japanese, Arabic, Russian, etc.)
   - HTML/SQL injection attempts
   - XSS payload attempts

3. **Formatting Issues**
   - Quoted fields with escaped quotes
   - Newlines within fields
   - Tab characters
   - Leading/trailing spaces
   - Control characters

4. **Data Variations**
   - Duplicate titles (should test deduplication)
   - Very long titles/content
   - Only numbers or special symbols
   - Mixed case variations

5. **Encoding Tests**
   - UTF-8 characters
   - HTML entities
   - Null bytes
   - Windows CRLF line endings

**Usage:**
```bash
# Test error handling with edge case data
python -m pytest backend/tests/integration/test_csv_validation.py

# Manually test CSV parsing
python scripts/test_csv_parser.py < tickets_edge_cases.csv
```

### Sample Markdown Outputs

These files show examples of what the AI-generated content should look like.

#### `draft_example.md`
**Purpose:** Example of AI-generated draft article
**Shows:**
- Problem/symptom description
- Root cause analysis
- Step-by-step solution
- Workaround information
- Prevention tips
- Related articles/links
- Support escalation path

**Use for:**
- Acceptance testing (does generated content match this format?)
- Training documentation reviewers
- Customer preview of AI quality

#### `clustering_groups.md`
**Purpose:** Example output of automated ticket clustering
**Shows:**
- How 100 tickets are grouped into 9 clusters
- Cluster naming and categorization
- Confidence scores for each cluster
- Summary and insights
- Resource allocation recommendations

**Use for:**
- Understanding expected clustering behavior
- Validating that clustering service groups similar issues
- Training team on ticket categorization logic

#### `published_article_example.md`
**Purpose:** Example of final published article on microsite
**Shows:**
- Professional formatting with headers
- Code examples with syntax highlighting
- Implementation phases and steps
- Performance metrics/benchmarks
- Testing procedures
- Browser compatibility matrix
- FAQ section
- Support and escalation information

**Use for:**
- End-to-end flow validation (draft → published)
- Article quality standards reference
- User documentation example

## How to Use These Fixtures

### In Integration Tests

```python
import csv
from pathlib import Path

# Load sample data
fixtures_dir = Path(__file__).parent.parent / 'fixtures'
sample_csv = fixtures_dir / 'tickets_sample.csv'

# Read and process
with open(sample_csv) as f:
    reader = csv.DictReader(f)
    tickets = list(reader)
    assert len(tickets) == 100
```

### In Manual Testing

```bash
# Upload sample tickets via API
curl -F "file=@backend/tests/fixtures/tickets_sample.csv" \
  http://localhost:8000/api/csv/upload

# Expected response
{
  "ticket_count": 100,
  "ticket_ids": ["tick_xxx", "tick_yyy", ...],
  "status": "uploaded_and_clustered",
  "clustering": {
    "total_tickets": 100,
    "clusters_created": 9,
    "clusters": [...]
  }
}
```

### In Load Testing

```bash
# Generate large dataset from sample
python scripts/generate_csv.py --base=tickets_sample.csv --multiply=10 --output=large_test.csv
# Creates 1000 entries (sample x 10)

# Upload and measure performance
time curl -F "file=@large_test.csv" http://localhost:8000/api/csv/upload
```

## Data Categories Mapping

### Cluster 1: Authentication (10 tickets)
Covers SSO, 2FA, password reset, session management issues

### Cluster 2: Performance (15 tickets)
Covers slow loading, API degradation, database optimization

### Cluster 3: Frontend (10 tickets)
Covers UI/UX, responsive design, accessibility

### Cluster 4: API & Integration (15 tickets)
Covers webhooks, OAuth, APIs, rate limiting

### Cluster 5-9: Features & Bugs (50 tickets)
Mix of feature requests, bug reports, documentation gaps

## Expected Clustering Output

When clustering the 100-entry sample, expect:
- **9 main clusters** formed automatically
- **Cluster confidence scores** 0.85-0.94
- **Even distribution** across categories
- **Clear thematic grouping** of related issues

## Edge Cases Covered

The edge case file includes:
- ✅ Missing fields (empty title/content)
- ✅ Unicode/emoji characters
- ✅ HTML/SQL injection attempts
- ✅ XSS payloads
- ✅ Duplicate entries
- ✅ Very long strings
- ✅ Special characters and symbols
- ✅ Mixed character encodings
- ✅ Whitespace variations
- ✅ Line break handling

## Validation Checklist

When testing CSV import with these fixtures:

- [ ] All 100 sample tickets imported successfully
- [ ] Tickets have correct status (UPLOADED)
- [ ] Clustering groups tickets into ~9 clusters
- [ ] Edge case CSV is rejected with proper error
- [ ] Special characters are preserved in database
- [ ] Duplicate detection works properly
- [ ] Empty fields are handled gracefully
- [ ] Very long content is truncated appropriately
- [ ] Unicode characters display correctly
- [ ] Performance is acceptable (<5 seconds for 100 tickets)

## Adding More Fixtures

To add new test data:

1. Create CSV in this directory
2. Follow format: `title,content` headers
3. Keep realistic data (avoid lorem ipsum)
4. Document purpose in this README
5. Add to test suite if needed

### New Fixture Template

```csv
title,content
Issue Title Here,Detailed description of the issue including symptoms and context
Related Feature,Request or description of desired functionality
```

## References

- **CSV Format:** RFC 4180 (https://tools.ietf.org/html/rfc4180)
- **Markdown Format:** CommonMark (https://spec.commonmark.org/)
- **Testing Guide:** See `backend/tests/integration/README.md`
- **API Documentation:** See `API_CONTRACTS.md` (project root)

## Support

For questions about test fixtures:
1. Check the test files using these fixtures
2. Review integration test documentation
3. Contact the backend team

---

**Last Updated:** 2025-11-17
**Status:** Ready for Use
**Coverage:** Kanban 2 Mock Data Requirements
