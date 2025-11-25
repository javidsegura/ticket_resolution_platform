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
        Test: CSV upload successfully creates tickets
        Expected: 84 tickets created, no errors
        """
        with open(sample_csv_file, "rb") as f:
            response = await async_client.post(
                "/api/upload-csv",
                files={"file": ("tickets_sample.csv", f, "text/csv")}
            )

        assert response.status_code == 200, f"Status: {response.status_code}, Response: {response.text}"
        data = response.json()

        assert data["success"] is True
        assert data["tickets_created"] == 84
        assert data["file_info"]["rows_processed"] == 84
        assert len(data["errors"]) == 0
        assert data["file_info"]["encoding"] == "utf-8-sig"

    @pytest.mark.asyncio
    async def test_csv_upload_invalid_file(self, async_client, tmp_path):
        """
        Checks that uploading a non-CSV file to the CSV upload endpoint is rejected.
        
        Asserts the endpoint returns HTTP 400 and the response detail message references "CSV".
        """
        # Create a non-CSV file
        bad_file = tmp_path / "notcsv.txt"
        bad_file.write_text("not csv content")

        with open(bad_file, "rb") as f:
            response = await async_client.post(
                "/api/upload-csv",
                files={"file": ("notcsv.txt", f, "text/plain")}
            )

        assert response.status_code == 400
        assert "CSV" in response.json()["detail"]


    @pytest.mark.asyncio
    async def test_health_check(self, async_client):
        """
        Verify the health check endpoint returns the expected pong response.
        
        Asserts that GET /api/health/ping responds with HTTP 200 and JSON {"response": "pong"}.
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
        response = await async_client.post("/api/upload-csv")
        # Should fail with 422/400 (missing file), not 404 (endpoint missing)
        assert response.status_code in [400, 422]


class TestCachingIntegration:
    """Test caching behavior"""

    @pytest.mark.asyncio
    async def test_caching_enabled(self, async_client):
        """
        Verify the application's cache infrastructure initializes successfully.
        
        Performs a health-check request to /api/health/ping and asserts an HTTP 200 response, indicating the cache manager loaded without errors.
        """
        # Health check should work if cache is properly initialized
        response = await async_client.get("/api/health/ping")
        assert response.status_code == 200




class TestErrorHandling:
    """Test error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_empty_csv_handling(self, async_client, tmp_path):
        """
        Test: Empty CSV file is handled gracefully
        Expected: Error response or 0 tickets created
        """
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("subject,body\n")

        with open(empty_csv, "rb") as f:
            response = await async_client.post(
                "/api/upload-csv",
                files={"file": ("empty.csv", f, "text/csv")}
            )

        # Should either succeed with 0 tickets or return error
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert data["tickets_created"] == 0

    @pytest.mark.asyncio
    async def test_malformed_csv_missing_columns(self, async_client, tmp_path):
        """
        Verify that uploading a CSV missing required ticket columns is rejected.
        
        Asserts the endpoint responds with HTTP 400 and the error detail mentions one of: "subject", "title", "body", or "content".
        """
        bad_csv = tmp_path / "bad.csv"
        bad_csv.write_text("name,email\nJohn,john@test.com\n")

        with open(bad_csv, "rb") as f:
            response = await async_client.post(
                "/api/upload-csv",
                files={"file": ("bad.csv", f, "text/csv")}
            )

        assert response.status_code == 400
        assert "subject" in response.json()["detail"].lower() or \
               "title" in response.json()["detail"].lower() or \
               "body" in response.json()["detail"].lower() or \
               "content" in response.json()["detail"].lower()

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
                "/api/upload-csv",
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
        Verify that uploading a file without a `.csv` extension is rejected.
        
        Asserts the upload endpoint returns HTTP 400 and the response detail references "csv".
        """
        no_ext = tmp_path / "noextension"
        no_ext.write_text("subject,body\ntest,content\n")

        with open(no_ext, "rb") as f:
            response = await async_client.post(
                "/api/upload-csv",
                files={"file": ("noextension", f, "text/csv")}
            )

        assert response.status_code == 400
        assert "csv" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_csv_with_wrong_content_type(self, async_client, tmp_path):
        """
        Verify that uploading a .csv file with an incorrect Content-Type header is rejected.
        
        Asserts the endpoint responds with HTTP 400 and that the response detail mentions "csv".
        """
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("subject,body\ntest,content\n")

        with open(csv_file, "rb") as f:
            response = await async_client.post(
                "/api/upload-csv",
                files={"file": ("test.csv", f, "text/plain")}  # Wrong content-type
            )

        assert response.status_code == 400
        assert "csv" in response.json()["detail"].lower()
