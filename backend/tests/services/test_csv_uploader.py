"""Tests for CSV uploader (database saving)"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.services.csv_uploader.csv_uploader import save_tickets_to_db
from ai_ticket_platform.database.generated_models import Ticket


class TestSaveTicketsToDb:
    """Test save_tickets_to_db function"""

    @pytest.fixture
    def sample_tickets_data(self):
        """Sample parsed ticket data from CSV parser"""
        return [
            {
                "subject": "Test Subject 1",
                "body": "Test Body 1",
                "id": "1",
                "created_at": "2024-01-01"
            },
            {
                "subject": "Test Subject 2",
                "body": "Test Body 2",
                "id": "2",
                "created_at": "2024-01-02"
            }
        ]

    @pytest.mark.asyncio
    async def test_save_valid_tickets(self, sample_tickets_data):
        """Test saving valid tickets to database"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        # Mock the CRUD function to return created tickets
        with patch('ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets') as mock_create:
            mock_tickets = [
                MagicMock(spec=Ticket, id=1, subject="Test Subject 1"),
                MagicMock(spec=Ticket, id=2, subject="Test Subject 2")
            ]
            mock_create.return_value = mock_tickets
            
            result = await save_tickets_to_db(mock_db, sample_tickets_data)
            
            assert len(result) == 2
            assert result[0].id == 1
            mock_create.assert_called_once_with(mock_db, sample_tickets_data)

    @pytest.mark.asyncio
    async def test_save_empty_tickets_raises_error(self):
        """Test error when tickets list is empty"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        with pytest.raises(ValueError) as exc:
            await save_tickets_to_db(mock_db, [])
        
        assert "No tickets data to save" in str(exc.value)

    @pytest.mark.asyncio
    async def test_save_none_tickets_raises_error(self):
        """Test error when tickets is None"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        with pytest.raises(ValueError):
            await save_tickets_to_db(mock_db, None)

    @pytest.mark.asyncio
    async def test_database_error_handling(self, sample_tickets_data):
        """Test error handling for database errors"""
        mock_db = AsyncMock(spec=AsyncSession)
        
        with patch('ai_ticket_platform.services.csv_uploader.csv_uploader.create_tickets') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            with pytest.raises(RuntimeError) as exc:
                await save_tickets_to_db(mock_db, sample_tickets_data)
            
            assert "Failed to save tickets" in str(exc.value)