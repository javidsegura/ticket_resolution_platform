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
            "/api/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "file_info" in data
        assert "tickets_created" in data
        assert "clustering" in data

    @pytest.mark.asyncio
    async def test_csv_upload_accepts_application_csv_content_type(self, async_client):
        """
        Verify that uploading a CSV file with the `application/csv` content type is accepted and returns the expected response schema.
        
        Asserts that the HTTP status code is 200 and that the JSON response contains at least the `success` and `file_info` keys.
        """
        csv_content = b"subject,body\nBug,Description\nIssue,Another problem\nFeature,Something cool"
        response = await async_client.post(
            "/api/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "application/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "file_info" in data

    @pytest.mark.asyncio
    async def test_csv_upload_response_has_correct_schema(self, async_client):
        """
        Verify that uploading a valid CSV returns a JSON response matching the expected schema.
        
        The response JSON must include top-level keys `success`, `file_info`, `tickets_created`, `clustering`, and `errors`. `file_info` must contain `filename`, `rows_processed`, `rows_skipped`, `tickets_extracted`, and `encoding`. `clustering` must contain `clusters_created` and `total_tickets_clustered`. The HTTP response Content-Type must be `application/json`.
        """
        csv_content = b"subject,body\nTest,Description\nAnother,More content here\nThird,Yet another ticket"
        response = await async_client.post(
            "/api/upload-csv",
            files={"file": ("test.csv", io.BytesIO(csv_content), "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()

        # Check for required response schema fields
        assert "success" in data
        assert "file_info" in data
        assert "tickets_created" in data
        assert "clustering" in data
        assert "errors" in data

        # Validate file_info structure
        file_info = data["file_info"]
        assert "filename" in file_info
        assert "rows_processed" in file_info
        assert "rows_skipped" in file_info
        assert "tickets_extracted" in file_info
        assert "encoding" in file_info

        # Validate clustering structure
        clustering = data["clustering"]
        assert "clusters_created" in clustering
        assert "total_tickets_clustered" in clustering

        assert response.headers.get("content-type") == "application/json"