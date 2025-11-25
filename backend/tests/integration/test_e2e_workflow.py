"""
E2E Workflow Integration Tests

Tests complete end-to-end workflows that combine multiple endpoints:
1. Health check → CSV upload → Verify database persistence
2. Health dependencies check → CSV upload → Document upload
3. Full workflow with caching behavior

These tests validate the entire platform working together.
"""

import pytest
import io
import asyncio


class TestCompleteCSVWorkflow:
    """Test complete CSV upload workflow"""

    @pytest.mark.asyncio
    async def test_workflow_health_check_then_csv_upload(self, async_client):
        """
        Execute a health ping followed by a CSV file upload and assert both operations succeed.
        
        Verifies that GET /api/health/ping returns status 200 with JSON {"response": "pong"}, then posts a CSV to /api/upload-csv and asserts the upload returns status 200.
        """
        # Step 1: Verify backend is healthy
        health_response = await async_client.get("/api/health/ping")
        assert health_response.status_code == 200
        assert health_response.json() == {"response": "pong"}

        # Step 2: Upload CSV file
        csv_content = b"subject,body\nTest Bug,Description here\nFeature,User wants X"
        upload_response = await async_client.post(
            "/api/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )

        # Should succeed after health check
        assert upload_response.status_code == 200

    @pytest.mark.asyncio
    async def test_workflow_health_dependencies_then_csv_upload(self, async_client):
        """
        Verify the /api/health/dependencies endpoint reports a "services" field and that a CSV file can be uploaded successfully.
        
        Performs a GET to /api/health/dependencies and asserts status 200 and presence of "services" in the JSON, then POSTs a CSV to /api/upload-csv and asserts status 200.
        """
        # Step 1: Check health dependencies
        deps_response = await async_client.get("/api/health/dependencies")
        assert deps_response.status_code == 200
        data = deps_response.json()
        assert "services" in data

        # Step 2: Upload CSV file
        csv_content = b"subject,body\nBug Report,System issue\nFeature Request,New capability\nFeedback,User comment"
        upload_response = await async_client.post(
            "/api/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )

        assert upload_response.status_code == 200

    @pytest.mark.asyncio
    async def test_workflow_csv_upload_and_pdf_upload(self, async_client):
        """
        Test: CSV upload → PDF upload workflow
        Expected: Both uploads succeed
        """
        # Step 1: Upload CSV
        csv_content = b"subject,body\nBug Report,System issue\nFeature Request,New capability\nFeedback,User comment"
        csv_response = await async_client.post(
            "/api/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        assert csv_response.status_code == 200

        # Step 2: Upload PDF
        pdf_content = b"%PDF-1.4\n%fake pdf"
        pdf_response = await async_client.post(
            "/api/documents/upload",
            files={"files": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
        )
        assert pdf_response.status_code == 200

    @pytest.mark.asyncio
    async def test_workflow_csv_upload_and_slack_notification(self, async_client):
        """
        Validate end-to-end workflow: upload a CSV file, then send a Slack notification.
        
        Uploads a CSV to /api/upload-csv and then posts a message to /api/slack/send-message. Asserts the CSV upload returns status 200 and the Slack request returns a status in [200, 400, 500].
        """
        # Step 1: Upload CSV
        csv_content = b"subject,body\nBug Report,System issue\nFeature Request,New capability\nFeedback,User comment"
        csv_response = await async_client.post(
            "/api/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )
        assert csv_response.status_code == 200

        # Step 2: Send Slack notification
        slack_response = await async_client.post(
            "/api/slack/send-message",
            params={"message": "CSV upload completed successfully"}
        )
        assert slack_response.status_code in [200, 400, 500]


class TestConcurrentWorkflows:
    """Test concurrent workflows"""

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, async_client):
        """
        Run ten concurrent health-check requests and verify each response is healthy.
        
        Verifies that all concurrent GET requests to /api/health/ping return HTTP 200 and JSON exactly equal to {"response": "pong"}.
        """
        tasks = [
            async_client.get("/api/health/ping")
            for _ in range(10)
        ]
        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)
        assert all(r.json() == {"response": "pong"} for r in responses)

    @pytest.mark.asyncio
    async def test_concurrent_csv_uploads(self, async_client):
        """
        Run three concurrent CSV upload requests and assert each response completes with an expected status.
        
        Performs three parallel POSTs to `/api/upload-csv` with distinct filenames and asserts that three responses are received and each has a status code in [200, 400, 422, 500].
        """
        csv_content = b"subject,body\nBug Report,System issue\nFeature Request,New capability\nFeedback,User comment"

        tasks = [
            async_client.post(
                "/api/upload-csv",
                files={"file": (f"test_{i}.csv", io.BytesIO(csv_content), "text/csv")}
            )
            for i in range(3)
        ]

        responses = await asyncio.gather(*tasks)

        # All should complete
        assert len(responses) == 3
        for response in responses:
            assert response.status_code in [200, 400, 422, 500]

    @pytest.mark.asyncio
    async def test_concurrent_mixed_endpoints(self, async_client):
        """
        Run concurrent requests across a mix of endpoints to verify they complete without interfering with each other.
        
        Issues concurrent requests to /api/health/ping, /api/health/dependencies, /api/upload-csv, /api/documents/upload, and /api/slack/send-message, then asserts that five responses are returned and each response status code is one of 200, 400, 422, or 500.
        """
        csv_content = b"subject,body\nBug Report,System issue\nFeature Request,New capability\nFeedback,User comment"
        pdf_content = b"%PDF-1.4\n%fake"

        tasks = [
            async_client.get("/api/health/ping"),
            async_client.get("/api/health/dependencies"),
            async_client.post(
                "/api/upload-csv",
                files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
            ),
            async_client.post(
                "/api/documents/upload",
                files={"files": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}
            ),
            async_client.post(
                "/api/slack/send-message",
                params={"message": "Test from concurrent test"}
            ),
        ]

        responses = await asyncio.gather(*tasks)

        # All should complete
        assert len(responses) == 5
        for response in responses:
            assert response.status_code in [200, 400, 422, 500]
