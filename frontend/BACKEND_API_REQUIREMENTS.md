# Backend API Requirements for Ticket Resolution Platform Frontend

## Overview

This document outlines all API endpoints required by the frontend to make the Ticket Resolution Platform fully functional. The frontend is built with React + TypeScript and currently uses dummy data that needs to be replaced with real backend API calls.

---

## Frontend Implementation Summary

### Current Features

1. **Dashboard Page**
   - Statistics cards (Total Tickets, Pending, Resolved, Avg Resolution Time)
   - Ticket Clusters section (compact list, expandable modal with filters)
   - Recent Tickets section (compact list, expandable modal with filters)
   - Global search bar (searches across tickets and clusters)
   - CSV upload functionality

2. **Cluster Detail Page**
   - View cluster information (title, summary, ticket count, status, priority, dates)
   - Display AI-generated resolution (markdown format, scrollable)
   - Action buttons: Approve, Give Feedback, Decline/Delete
   - Download options (Markdown, HTML)
   - Feedback form modal (for reprompting AI)

3. **Ticket Detail Page** (View-only)
   - View ticket information (title, customer, created date)
   - Display customer question
   - Download options (Markdown, HTML)

### Authentication

- Currently uses Firebase Authentication (frontend handles this)
- Backend may need to validate Firebase tokens if required
- API calls should include `Authorization: Bearer <token>` header when auth is required

---

## Required API Endpoints

### Base URL Configuration

The frontend expects the base API URL to be configured via environment variable:
- `VITE_BASE_URL` - Base URL for the backend API (e.g., `http://localhost:8000` or `https://api.example.com`)

---

## 1. Clusters Endpoints

### 1.1 GET /api/clusters

**Description:** Fetch all ticket clusters

**Request:**
- Method: `GET`
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional, if auth required)

**Query Parameters (optional for filtering):**
- `priority`: `"all" | "high" | "medium" | "low"` (default: "all")
- `status`: `"all" | "active" | "pending" | "resolved"` (default: "all")
- `search`: `string` - Search term to filter by title or summary (default: empty)

**Response:**
- Status: `200 OK`
- Body: `Cluster[]` (array of cluster objects)

**Example Response:**
```json
[
  {
    "id": "cluster-1",
    "title": "Password Reset Issues",
    "summary": "Multiple customers are experiencing difficulties with password reset functionality...",
    "ticketCount": 12,
    "createdAt": "2024-01-10T08:00:00Z",
    "updatedAt": "2024-01-15T14:30:00Z",
    "mainTopics": [
      "Password reset link location",
      "Email delivery issues",
      "Reset instructions clarity"
    ],
    "priority": "high",
    "status": "active",
    "resolution": "**Website Improvement Recommendation:**\n\nAdd a prominent..."
  }
]
```

**Cluster Interface:**
```typescript
interface Cluster {
  id: string
  title: string
  summary: string
  ticketCount: number
  createdAt: string // ISO 8601 format
  updatedAt: string // ISO 8601 format
  mainTopics: string[]
  priority: "high" | "medium" | "low"
  status: "active" | "resolved" | "pending"
  resolution?: string // Markdown format, optional
}
```

---

### 1.2 GET /api/clusters/:id

**Description:** Fetch a single cluster by ID

**Request:**
- Method: `GET`
- Path Parameter: `id` (string) - Cluster ID
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional)

**Response:**
- Status: `200 OK` - Returns cluster object
- Status: `404 Not Found` - Cluster not found
- Body: `Cluster` (single cluster object)

**Example Response:**
```json
{
  "id": "cluster-1",
  "title": "Password Reset Issues",
  "summary": "Multiple customers are experiencing difficulties...",
  "ticketCount": 12,
  "createdAt": "2024-01-10T08:00:00Z",
  "updatedAt": "2024-01-15T14:30:00Z",
  "mainTopics": ["Password reset link location", "Email delivery issues"],
  "priority": "high",
  "status": "active",
  "resolution": "**Website Improvement Recommendation:**\n\n..."
}
```

---

### 1.3 POST /api/clusters/:id/feedback

**Description:** Submit feedback to reprompt the AI assistant and regenerate the resolution

**Request:**
- Method: `POST`
- Path Parameter: `id` (string) - Cluster ID
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional)

**Request Body:**
```json
{
  "feedback": "Please make the recommendations more technical and include specific implementation steps. Also, add a section about security considerations."
}
```

**Validation Rules:**
- `feedback` (required): string, minimum 10 characters
- Cluster must not be in "resolved" status

**Response:**
- Status: `200 OK` - Feedback accepted, AI regeneration started
- Status: `400 Bad Request` - Invalid feedback or cluster already resolved
- Status: `404 Not Found` - Cluster not found

**Example Response:**
```json
{
  "message": "Feedback received. AI assistant is regenerating the resolution.",
  "clusterId": "cluster-1",
  "status": "processing"
}
```

**Note:** After submission, the frontend may poll or receive a webhook notification when the new resolution is ready. Alternatively, the resolution can be refetched via GET /api/clusters/:id

---

### 1.4 POST /api/clusters/:id/approve

**Description:** Approve a cluster (marks it as resolved)

**Request:**
- Method: `POST`
- Path Parameter: `id` (string) - Cluster ID
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional)

**Request Body:** None (or empty object `{}`)

**Validation Rules:**
- Cluster must not already be in "resolved" status

**Response:**
- Status: `200 OK` - Cluster approved
- Status: `400 Bad Request` - Cluster already resolved
- Status: `404 Not Found` - Cluster not found

**Example Response:**
```json
{
  "message": "Cluster approved successfully",
  "clusterId": "cluster-1",
  "status": "resolved"
}
```

---

### 1.5 DELETE /api/clusters/:id (or POST /api/clusters/:id/decline)

**Description:** Decline/Delete a cluster

**Request:**
- Method: `DELETE` (or `POST /api/clusters/:id/decline`)
- Path Parameter: `id` (string) - Cluster ID
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional)

**Request Body:** None

**Validation Rules:**
- Cluster must not already be in "resolved" status

**Response:**
- Status: `200 OK` - Cluster declined/deleted
- Status: `204 No Content` - Cluster deleted (no body)
- Status: `400 Bad Request` - Cluster already resolved
- Status: `404 Not Found` - Cluster not found

**Example Response (if DELETE returns body):**
```json
{
  "message": "Cluster declined and deleted successfully",
  "clusterId": "cluster-1"
}
```

---

## 2. Tickets Endpoints

### 2.1 GET /api/tickets

**Description:** Fetch all tickets

**Request:**
- Method: `GET`
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional)

**Query Parameters (optional for filtering):**
- `search`: `string` - Search term to filter by title or customer email (default: empty)
- `limit`: `number` - Limit number of results (optional, for pagination)
- `offset`: `number` - Offset for pagination (optional)

**Note:** The frontend only displays ticket title and customer - it does NOT show status or priority in the UI. The frontend performs client-side filtering by search term only (searching title and customer email). Backend does NOT need to support priority/status filtering for tickets unless needed for future features. Just return all tickets (or filter by search if implemented), and the frontend will handle the rest.

**Response:**
- Status: `200 OK`
- Body: `Ticket[]` (array of ticket objects)

**Example Response:**
```json
[
  {
    "id": "1",
    "title": "How do I reset my password?",
    "customer": "john.doe@example.com",
    "createdAt": "2024-01-15T10:30:00Z",
    "question": "I forgot my password and can't find the reset link on your website. Where should I look?"
  }
]
```

**Ticket Interface (for list view):**
```typescript
interface Ticket {
  id: string
  title: string
  customer: string // Email address
  createdAt: string // ISO 8601 format
  question: string
}
```

**Note:** The frontend does not display status or priority for tickets on the dashboard, but they may be stored in the backend for other purposes.

---

### 2.2 GET /api/tickets/:id

**Description:** Fetch a single ticket by ID

**Request:**
- Method: `GET`
- Path Parameter: `id` (string) - Ticket ID
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional)

**Response:**
- Status: `200 OK` - Returns ticket object
- Status: `404 Not Found` - Ticket not found
- Body: `TicketDetail` (single ticket detail object)

**Example Response:**
```json
{
  "id": "1",
  "title": "How do I reset my password?",
  "customer": "john.doe@example.com",
  "createdAt": "2024-01-15T10:30:00Z",
  "question": "I forgot my password and can't find the reset link on your website. Where should I look?"
}
```

**Ticket Detail Interface:**
```typescript
interface TicketDetail {
  id: string
  title: string
  customer: string // Email address
  createdAt: string // ISO 8601 format
  question: string // The customer's original question/issue
}
```

**Note:** The ticket detail page is view-only and does not need resolution or status/priority fields.

---

### 2.3 POST /api/tickets/upload-csv

**Description:** Upload a CSV file containing tickets for processing

**Request:**
- Method: `POST`
- Headers:
  - `Authorization: Bearer <token>` (optional)
  - Note: Do NOT set `Content-Type: application/json` - browser will set `multipart/form-data`

**Request Body:**
- Form Data with field name: `file`
- File type: CSV file
- Content-Type: `multipart/form-data`

**Expected CSV Format:**
The CSV should contain tickets with at least the following columns:
- `id` or `ticket_id` - Unique ticket identifier
- `title` or `subject` - Ticket title/subject
- `customer` or `email` or `customer_email` - Customer email address
- `question` or `description` or `message` - The customer's question/issue
- `created_at` or `created` or `timestamp` - Creation timestamp (ISO 8601 or parseable date format)

**Response:**
- Status: `200 OK` - CSV uploaded and processing started
- Status: `400 Bad Request` - Invalid CSV format or file
- Status: `413 Payload Too Large` - File too large

**Example Response:**
```json
{
  "message": "CSV file uploaded successfully. Processing tickets...",
  "uploadId": "upload-123",
  "ticketCount": 24,
  "status": "processing"
}
```

**Error Response Example:**
```json
{
  "error": "Invalid CSV format",
  "details": "Missing required columns: customer, question"
}
```

---

## 3. Statistics/Dashboard Endpoints

### 3.1 GET /api/dashboard/stats

**Description:** Fetch dashboard statistics

**Request:**
- Method: `GET`
- Headers:
  - `Content-Type: application/json`
  - `Authorization: Bearer <token>` (optional)

**Response:**
- Status: `200 OK`
- Body: `DashboardStats` object

**Example Response:**
```json
{
  "totalTickets": 24,
  "pendingTickets": 8,
  "resolvedTickets": 12,
  "avgResolutionTime": "2.5 hours"
}
```

**Dashboard Stats Interface:**
```typescript
interface DashboardStats {
  totalTickets: number
  pendingTickets: number
  resolvedTickets: number
  avgResolutionTime: string // Formatted string like "2.5 hours" or "45 minutes"
}
```

---

**Note on Global Search:** The global search bar in the dashboard header is implemented entirely in the frontend. It searches through clusters and tickets that have already been fetched via the respective GET endpoints. No separate backend search endpoint is required - the frontend performs client-side filtering on already-loaded data.

---

## Error Handling

### Standard Error Response Format

All endpoints should return errors in a consistent format:

```json
{
  "error": "Error message",
  "details": "Additional error details (optional)",
  "code": "ERROR_CODE" // Optional error code
}
```

### HTTP Status Codes

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `204 No Content` - Successful deletion (no body)
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `500 Internal Server Error` - Server error

### Validation Errors

When validation fails, return:
```json
{
  "error": "Validation failed",
  "details": {
    "field_name": ["Error message for this field"]
  }
}
```

---

## Authentication

### Authorization Header

If authentication is required, the frontend will include:
```
Authorization: Bearer <firebase_token>
```

The backend should:
1. Validate the Firebase token
2. Extract user information if needed
3. Return `401 Unauthorized` if token is invalid or missing

---

## Data Formats

### Date/Time Format
- All dates should be in ISO 8601 format: `YYYY-MM-DDTHH:mm:ssZ`
- Example: `"2024-01-15T10:30:00Z"`

### Markdown Format
- The `resolution` field in clusters should be valid markdown
- Frontend uses `react-markdown` to render it

### Priority Values
- Clusters: `"high" | "medium" | "low"`
- Tickets: Can use same values (though not displayed in UI)

### Status Values
- Clusters: `"active" | "pending" | "resolved"`
- Tickets: `"pending" | "in_review" | "resolved" | "declined"` (stored but not displayed)

---

## CORS Configuration

The backend must allow CORS requests from the frontend origin:
- Allow headers: `Content-Type`, `Authorization`
- Allow methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- Allow credentials if authentication is used

---

## Environment Variables

The frontend requires:
- `VITE_BASE_URL` - Base URL for backend API (e.g., `http://localhost:8000` or `https://api.example.com`)

---

## Testing Notes

Currently, the frontend:
- Falls back to dummy data if `VITE_BASE_URL` is not configured
- Falls back to dummy data if API calls fail
- Uses mock Firebase authentication if credentials are not available

To test with real backend:
1. Set `VITE_BASE_URL` environment variable
2. Ensure backend is running and accessible
3. Frontend will automatically use real API calls instead of dummy data

---

## Summary Table

| Endpoint | Method | Purpose | Request Body/Params | Response |
|----------|--------|---------|---------------------|----------|
| `/api/clusters` | GET | Get all clusters | Query: `priority`, `status`, `search` | `Cluster[]` |
| `/api/clusters/:id` | GET | Get single cluster | None | `Cluster` |
| `/api/clusters/:id/feedback` | POST | Submit feedback | `{feedback: string}` | `{message, status}` |
| `/api/clusters/:id/approve` | POST | Approve cluster | None | `{message, status}` |
| `/api/clusters/:id/decline` | DELETE/POST | Decline cluster | None | `{message}` or 204 |
| `/api/tickets` | GET | Get all tickets | Query: `search` (optional) | `Ticket[]` |
| `/api/tickets/:id` | GET | Get single ticket | None | `TicketDetail` |
| `/api/tickets/upload-csv` | POST | Upload CSV | Form data (file) | `{message, uploadId}` |
| `/api/dashboard/stats` | GET | Get dashboard stats | None | `DashboardStats` |

---

## Next Steps

1. **Backend Team:** Implement these endpoints according to the specifications above
2. **Frontend Team:** Will update API service files once endpoints are ready
3. **Testing:** Test endpoints with frontend once backend is available
4. **Authentication:** Coordinate on Firebase token validation if required
5. **CSV Format:** Finalize CSV column names and format with backend team

---

## Questions or Clarifications

If any endpoint requirements are unclear or need adjustment, please discuss with the frontend team before implementation to ensure compatibility.

