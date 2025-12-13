"""
E2E Integration Tests for CSV Upload

Tests the CSV upload pipeline against real Docker services:
- File validation (extension, content-type, size limits)
- Successful CSV upload and ticket creation
- Error handling (invalid files, malformed CSV, oversized files)
- Database persistence verification
- Caching behavior with Redis

These tests run against real MySQL, Redis when using: make test-integration-docker
"""

import pytest
from pathlib import Path
import io


class TestCSVUploadSuccess:
    """Test successful CSV uploads"""

    @pytest.mark.asyncio
    async def test_csv_upload_accepts_csv_with_correct_content_type(self, async_client):
        """
        Test: CSV file with text/csv content-type is accepted
        Expected: 200 OK response with proper schema
        """
        csv_content = b"subject,body\nTest Bug,Description here\nFeature Request,User wants X\nBug Report,System crash on startup\nFeedback,More features needed"
        response = await async_client.post(
            "/api/tickets/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        # Check for actual API response schema (queue-based)
        assert "message" in data
        assert "filename" in data
        assert "tickets_count" in data
        assert "jobs" in data

    @pytest.mark.asyncio
    async def test_csv_upload_accepts_application_csv_content_type(self, async_client):
        """
        Test: CSV file with application/csv content-type is accepted
        Expected: 200 OK response with proper schema
        """
        csv_content = b"subject,body\nBug,Description\nIssue,Another problem\nFeature,Something cool"
        response = await async_client.post(
            "/api/tickets/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "application/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        # Check for actual API response schema (queue-based)
        assert "message" in data
        assert "filename" in data

    @pytest.mark.asyncio
    async def test_csv_upload_response_has_correct_schema(self, async_client):
        """
        Test: Successful CSV upload returns proper response schema
        Expected: Response contains all required fields with correct structure
        """
        csv_content = b"subject,body\nTest,Description\nAnother,More content here\nThird,Yet another ticket"
        response = await async_client.post(
            "/api/tickets/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()

        # Check for actual API response schema (queue-based)
        assert "message" in data
        assert "filename" in data
        assert "tickets_count" in data
        assert "jobs" in data

        # Validate jobs structure
        jobs = data["jobs"]
        assert "batch_count" in jobs
        assert "stage1_job_count" in jobs
        assert "finalizer_job_id" in jobs
        assert "batch_size" in jobs

        assert response.headers.get("content-type") == "application/json"
