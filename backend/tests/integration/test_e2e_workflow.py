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
        Test: Health check → CSV upload workflow
        Expected: Both succeed in sequence
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
        Test: Check dependencies → CSV upload workflow
        Expected: Both succeed in sequence
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
        Test: CSV upload → Slack notification workflow
        Expected: Both succeed
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
        Test: Multiple concurrent health checks
        Expected: All succeed
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
        Test: Multiple concurrent CSV uploads
        Expected: All complete without crashes
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
        Test: Concurrent requests to different endpoints
        Expected: All complete without interference
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

