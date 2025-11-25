"""Unit tests for CSV orchestrator service."""

import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.services.csv_uploader.csv_orchestrator import upload_csv_file


@pytest.mark.asyncio
class TestUploadCSVFile:
    """Test the upload_csv_file orchestration function."""

    async def test_successful_csv_upload_workflow(self):
        """Test complete successful upload workflow: parse -> cluster -> save."""
        # Mock file upload
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "tickets.csv"

        # Mock file content as CSV
        csv_content = b"subject,body\nLogin Bug,Cannot login\nPassword Reset,Need reset\nPayment Issue,Card declined"
        mock_file.read = AsyncMock(side_effect=[csv_content, b""])  # Return content once, then empty

        # Mock database session
        mock_db = MagicMock(spec=AsyncSession)

        # Mock parse_csv_file
        mock_parse_result = {
            "success": True,
            "file_info": {
                "filename": "tickets.csv",
                "rows_processed": 3,
                "rows_skipped": 0,
                "tickets_extracted": 3,
                "encoding": "utf-8"
            },
            "tickets": [
                {"subject": "Login Bug", "body": "Cannot login"},
                {"subject": "Password Reset", "body": "Need reset"},
                {"subject": "Payment Issue", "body": "Card declined"}
            ],
            "errors": []
        }

        # Mock clustering
        mock_clustering_result = {
            "total_tickets": 3,
            "clusters_created": 2,
            "clusters": []
        }

        # Mock database save
        mock_tickets = [MagicMock(id=i) for i in range(1, 4)]

        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.parse_csv_file") as mock_parse:
            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.cluster_tickets_with_cache", new_callable=AsyncMock) as mock_cluster:
                with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.save_tickets_to_db", new_callable=AsyncMock) as mock_save:
                    with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.tempfile.NamedTemporaryFile") as mock_temp:
                        mock_parse.return_value = mock_parse_result
                        mock_cluster.return_value = mock_clustering_result
                        mock_save.return_value = mock_tickets

                        # Mock temp file
                        mock_tmp_file = MagicMock()
                        mock_tmp_file.name = "/tmp/test.csv"
                        mock_tmp_file.__enter__.return_value = mock_tmp_file
                        mock_tmp_file.__exit__.return_value = None
                        mock_temp.return_value = mock_tmp_file

                        result = await upload_csv_file(mock_file, mock_db)

                        assert result["success"] is True
                        assert result["tickets_created"] == 3
                        assert result["file_info"]["filename"] == "tickets.csv"
                        assert result["file_info"]["tickets_extracted"] == 3
                        assert result["clustering"]["clusters_created"] == 2

    async def test_csv_upload_with_invalid_csv(self):
        """Test that invalid CSV raises ValueError."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "invalid.csv"
        mock_file.read = AsyncMock(side_effect=[b"invalid,data\n", b""])

        mock_db = MagicMock(spec=AsyncSession)

        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.parse_csv_file") as mock_parse:
            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.tempfile.NamedTemporaryFile") as mock_temp:
                mock_parse.side_effect = ValueError("must contain either subject,body or title,content")

                mock_tmp_file = MagicMock()
                mock_tmp_file.name = "/tmp/test.csv"
                mock_tmp_file.__enter__.return_value = mock_tmp_file
                mock_tmp_file.__exit__.return_value = None
                mock_temp.return_value = mock_tmp_file

                with pytest.raises(ValueError, match="must contain either"):
                    await upload_csv_file(mock_file, mock_db)

    async def test_csv_upload_clustering_failure(self):
        """Test that clustering failure is propagated."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "tickets.csv"
        mock_file.read = AsyncMock(side_effect=[b"subject,body\nBug,Desc\n", b""])

        mock_db = MagicMock(spec=AsyncSession)

        mock_parse_result = {
            "success": True,
            "file_info": {"filename": "tickets.csv", "rows_processed": 1, "rows_skipped": 0, "tickets_extracted": 1, "encoding": "utf-8"},
            "tickets": [{"subject": "Bug", "body": "Desc"}],
            "errors": []
        }

        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.parse_csv_file") as mock_parse:
            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.cluster_tickets_with_cache") as mock_cluster:
                with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.tempfile.NamedTemporaryFile") as mock_temp:
                    mock_parse.return_value = mock_parse_result
                    mock_cluster.side_effect = RuntimeError("LLM clustering failed")

                    mock_tmp_file = MagicMock()
                    mock_tmp_file.name = "/tmp/test.csv"
                    mock_tmp_file.__enter__.return_value = mock_tmp_file
                    mock_tmp_file.__exit__.return_value = None
                    mock_temp.return_value = mock_tmp_file

                    with pytest.raises(RuntimeError, match="LLM clustering failed"):
                        await upload_csv_file(mock_file, mock_db)

    async def test_csv_upload_database_failure(self):
        """Test that database errors are propagated."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "tickets.csv"
        mock_file.read = AsyncMock(side_effect=[b"subject,body\nBug,Desc\n", b""])

        mock_db = MagicMock(spec=AsyncSession)

        mock_parse_result = {
            "success": True,
            "file_info": {"filename": "tickets.csv", "rows_processed": 1, "rows_skipped": 0, "tickets_extracted": 1, "encoding": "utf-8"},
            "tickets": [{"subject": "Bug", "body": "Desc"}],
            "errors": []
        }

        mock_clustering_result = {"total_tickets": 1, "clusters_created": 0, "clusters": []}

        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.parse_csv_file") as mock_parse:
            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.cluster_tickets_with_cache", new_callable=AsyncMock) as mock_cluster:
                with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.save_tickets_to_db", new_callable=AsyncMock) as mock_save:
                    with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.tempfile.NamedTemporaryFile") as mock_temp:
                        mock_parse.return_value = mock_parse_result
                        mock_cluster.return_value = mock_clustering_result
                        mock_save.side_effect = RuntimeError("Database connection failed")

                        mock_tmp_file = MagicMock()
                        mock_tmp_file.name = "/tmp/test.csv"
                        mock_tmp_file.__enter__.return_value = mock_tmp_file
                        mock_tmp_file.__exit__.return_value = None
                        mock_temp.return_value = mock_tmp_file

                        with pytest.raises(RuntimeError, match="Database connection failed"):
                            await upload_csv_file(mock_file, mock_db)

    async def test_csv_upload_temp_file_cleanup(self):
        """Test that temp file is cleaned up even on success."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "tickets.csv"
        mock_file.read = AsyncMock(side_effect=[b"subject,body\nBug,Desc\n", b""])

        mock_db = MagicMock(spec=AsyncSession)

        mock_parse_result = {
            "success": True,
            "file_info": {"filename": "tickets.csv", "rows_processed": 1, "rows_skipped": 0, "tickets_extracted": 1, "encoding": "utf-8"},
            "tickets": [{"subject": "Bug", "body": "Desc"}],
            "errors": []
        }

        mock_clustering_result = {"total_tickets": 1, "clusters_created": 0, "clusters": []}
        mock_tickets = [MagicMock(id=1)]

        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.parse_csv_file") as mock_parse:
            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.cluster_tickets_with_cache", new_callable=AsyncMock) as mock_cluster:
                with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.save_tickets_to_db", new_callable=AsyncMock) as mock_save:
                    with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.tempfile.NamedTemporaryFile") as mock_temp:
                        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.os.unlink") as mock_unlink:
                            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.os.path.exists") as mock_exists:
                                mock_parse.return_value = mock_parse_result
                                mock_cluster.return_value = mock_clustering_result
                                mock_save.return_value = mock_tickets
                                mock_exists.return_value = True

                                mock_tmp_file = MagicMock()
                                mock_tmp_file.name = "/tmp/test.csv"
                                mock_tmp_file.__enter__.return_value = mock_tmp_file
                                mock_tmp_file.__exit__.return_value = None
                                mock_temp.return_value = mock_tmp_file

                                result = await upload_csv_file(mock_file, mock_db)

                                assert result["success"] is True
                                mock_unlink.assert_called_once_with("/tmp/test.csv")

    async def test_csv_upload_temp_file_cleanup_on_error(self):
        """Test that temp file is cleaned up even on error."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "tickets.csv"
        mock_file.read = AsyncMock(side_effect=[b"subject,body\nBug,Desc\n", b""])

        mock_db = MagicMock(spec=AsyncSession)

        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.parse_csv_file") as mock_parse:
            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.tempfile.NamedTemporaryFile") as mock_temp:
                with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.os.unlink") as mock_unlink:
                    with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.os.path.exists") as mock_exists:
                        mock_parse.side_effect = ValueError("Invalid CSV")
                        mock_exists.return_value = True

                        mock_tmp_file = MagicMock()
                        mock_tmp_file.name = "/tmp/test.csv"
                        mock_tmp_file.__enter__.return_value = mock_tmp_file
                        mock_tmp_file.__exit__.return_value = None
                        mock_temp.return_value = mock_tmp_file

                        with pytest.raises(ValueError, match="Invalid CSV"):
                            await upload_csv_file(mock_file, mock_db)

                        # File should still be cleaned up
                        mock_unlink.assert_called_once_with("/tmp/test.csv")

    async def test_csv_upload_temp_file_cleanup_failure_ignored(self):
        """Test that temp file cleanup failures don't crash the upload."""
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "tickets.csv"
        mock_file.read = AsyncMock(side_effect=[b"subject,body\nBug,Desc\n", b""])

        mock_db = MagicMock(spec=AsyncSession)

        mock_parse_result = {
            "success": True,
            "file_info": {"filename": "tickets.csv", "rows_processed": 1, "rows_skipped": 0, "tickets_extracted": 1, "encoding": "utf-8"},
            "tickets": [{"subject": "Bug", "body": "Desc"}],
            "errors": []
        }

        mock_clustering_result = {"total_tickets": 1, "clusters_created": 0, "clusters": []}
        mock_tickets = [MagicMock(id=1)]

        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.parse_csv_file") as mock_parse:
            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.cluster_tickets_with_cache", new_callable=AsyncMock) as mock_cluster:
                with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.save_tickets_to_db", new_callable=AsyncMock) as mock_save:
                    with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.tempfile.NamedTemporaryFile") as mock_temp:
                        with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.os.unlink") as mock_unlink:
                            with patch("ai_ticket_platform.services.csv_uploader.csv_orchestrator.os.path.exists") as mock_exists:
                                mock_parse.return_value = mock_parse_result
                                mock_cluster.return_value = mock_clustering_result
                                mock_save.return_value = mock_tickets
                                mock_exists.return_value = True
                                # Cleanup fails but shouldn't crash
                                mock_unlink.side_effect = Exception("Permission denied")

                                mock_tmp_file = MagicMock()
                                mock_tmp_file.name = "/tmp/test.csv"
                                mock_tmp_file.__enter__.return_value = mock_tmp_file
                                mock_tmp_file.__exit__.return_value = None
                                mock_temp.return_value = mock_tmp_file

                                # Should still succeed despite cleanup failure
                                result = await upload_csv_file(mock_file, mock_db)
                                assert result["success"] is True
