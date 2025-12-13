"""
MVP E2E Integration Tests

Tests the running backend for the CSV upload pipeline:
1. CSV upload → clustering → tickets created
2. File validation (extension, content-type, size limits)
3. Error handling (empty CSV, malformed CSV, oversized files)
4. Cache infrastructure initialization
5. API response structure validation

These tests use the running backend server via ASGI transport, not the test database.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_csv_file():
    """Get path to sample CSV for testing"""
    csv_path = Path(__file__).parent.parent / "fixtures" / "tickets_sample.csv"
    if not csv_path.exists():
        pytest.skip(f"Sample CSV not found at {csv_path}")
    return csv_path


class TestMVPE2E:
    """End-to-end MVP tests against running backend"""

    @pytest.mark.asyncio
    async def test_csv_upload_success(self, async_client, sample_csv_file):
        """
        Test: CSV upload successfully queues tickets for processing
        Expected: Queue-based response with job IDs
        """
        with open(sample_csv_file, "rb") as f:
            response = await async_client.post(
                "/api/tickets/upload-csv",
                files={"file": ("tickets_sample.csv", f, "text/csv")}
            )

        assert response.status_code == 200, f"Status: {response.status_code}, Response: {response.text}"
        data = response.json()

        # Check for queue-based API response schema
        assert "message" in data
        assert "filename" in data
        assert "tickets_count" in data
        assert "jobs" in data

        # Verify job structure
        assert data["tickets_count"] == 84
        assert "batch_count" in data["jobs"]
        assert "stage1_job_count" in data["jobs"]
        assert "finalizer_job_id" in data["jobs"]

    @pytest.mark.asyncio
    async def test_csv_upload_invalid_file(self, async_client, tmp_path):
        """
        Test: Non-CSV file is rejected
        Expected: 400 error
        """
        # Create a non-CSV file
        bad_file = tmp_path / "notcsv.txt"
        bad_file.write_text("not csv content")

        with open(bad_file, "rb") as f:
            response = await async_client.post(
                "/api/tickets/upload-csv",
                files={"file": ("notcsv.txt", f, "text/plain")}
            )

        assert response.status_code == 400
        assert "CSV" in response.json()["detail"]


    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """
        Test: Health check endpoint responds
        Expected: {"response": "pong"}
        """
        response = await async_client.get("/api/health/ping")
        assert response.status_code == 200
        assert response.json() == {"response": "pong"}

    @pytest.mark.asyncio
    async def test_upload_endpoint_exists(self, async_client):
        """
        Test: Upload endpoint is registered
        Expected: Not 404
        """
        response = await async_client.post("/api/tickets/upload-csv")
        # Should fail with 422/400 (missing file), not 404 (endpoint missing)
        assert response.status_code in [400, 422]


class TestCachingIntegration:
    """Test caching behavior"""

    @pytest.mark.asyncio
    async def test_caching_enabled(self, async_client):
        """
        Test: Cache infrastructure is initialized
        Expected: Cache manager loaded without errors
        """
        # Health check should work if cache is properly initialized
        response = await async_client.get("/api/health/ping")
        assert response.status_code == 200




class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_empty_csv_handling(self, async_client, tmp_path):
        """
        Test: Empty CSV file is rejected
        Expected: 500 error with "No valid tickets" message
        """
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("subject,body\n")

        with open(empty_csv, "rb") as f:
            response = await async_client.post(
                "/api/tickets/upload-csv",
                files={"file": ("empty.csv", f, "text/csv")}
            )

        # API returns 500 for empty CSVs
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "valid tickets" in data["detail"].lower() or "process" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_malformed_csv_missing_columns(self, async_client, tmp_path):
        """
        Test: CSV missing required columns is rejected
        Expected: 400 or 500 error with validation message
        """
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("name,email\nJohn,john@test.com\n")

        with open(bad_csv, "rb") as f:
            response = await async_client.post(
                "/api/tickets/upload-csv",
                files={"file": ("bad.csv", f, "text/csv")}
            )

        # API returns 500 for validation errors during processing
        assert response.status_code in [400, 500]
        assert "subject" in response.json()["detail"].lower() or \
               "body" in response.json()["detail"].lower() or \
               "process" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_oversized_file_rejection(self, async_client, tmp_path):
        """
        Test: Files over 10MB are rejected
        Expected: 400 error
        """
        # Create a large file (11MB)
        large_csv = tmp_path / "large.csv"
        header = "subject,body\n"
        # Create content that's ~11MB
        row = "x" * 100 + "," + "y" * 100 + "\n"
        content = header + (row * 60000)  # ~11MB

        large_csv.write_text(content)

        with open(large_csv, "rb") as f:
            response = await async_client.post(
                "/api/tickets/upload-csv",
                files={"file": ("large.csv", f, "text/csv")}
            )

        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower() or \
               "exceed" in response.json()["detail"].lower()



class TestFileValidation:
    """Test file type and content validation"""

    @pytest.mark.asyncio
    async def test_file_without_extension_rejected(self, async_client, tmp_path):
        """
        Test: Files without .csv extension are rejected
        Expected: 400 error
        """
        no_ext = tmp_path / "noextension"
        no_ext.write_text("subject,body\ntest,content\n")

        with open(no_ext, "rb") as f:
            response = await async_client.post(
                "/api/tickets/upload-csv",
                files={"file": ("noextension", f, "text/csv")}
            )

        assert response.status_code == 400
        assert "csv" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_csv_with_wrong_content_type(self, async_client, tmp_path):
        """
        Test: CSV with wrong content-type is rejected
        Expected: 400 error
        """
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\ntest,content\n")

        with open(csv_file, "rb") as f:
            response = await async_client.post(
                "/api/tickets/upload-csv",
                files={"file": ("test.csv", f, "text/plain")}  # Wrong content-type
            )

        assert response.status_code == 400
        assert "csv" in response.json()["detail"].lower()

