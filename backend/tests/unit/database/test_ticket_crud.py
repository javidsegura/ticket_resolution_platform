"""Unit tests for ticket CRUD operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from ai_ticket_platform.database.CRUD.ticket import (
	create_tickets,
	get_ticket,
	list_tickets,
	count_tickets,
	list_tickets_by_intent,
	update_ticket_intent
)


@pytest.mark.asyncio
class TestCreateTickets:
	"""Test create_tickets bulk insert operation."""

	async def test_create_tickets_success(self):
		"""Test successful bulk creation of tickets."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add_all = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.rollback = AsyncMock()

		tickets_data = [
			{"subject": "Login Issue", "body": "Cannot login to app", "created_at": None},
			{"subject": "Payment Error", "body": "Payment failed", "created_at": datetime(2025, 1, 1)}
		]

		with patch("ai_ticket_platform.database.CRUD.ticket.Ticket") as mock_ticket_class:
			mock_ticket_1 = MagicMock()
			mock_ticket_2 = MagicMock()
			mock_ticket_class.side_effect = [mock_ticket_1, mock_ticket_2]

			result = await create_tickets(db=mock_db, tickets_data=tickets_data)

			assert len(result) == 2
			assert mock_ticket_class.call_count == 2
			mock_db.add_all.assert_called_once()
			mock_db.commit.assert_called_once()
			mock_db.rollback.assert_not_called()

	async def test_create_tickets_with_none_created_at(self):
		"""Test tickets created without created_at use database default."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add_all = MagicMock()
		mock_db.commit = AsyncMock()

		tickets_data = [{"subject": "Test", "body": "Test body", "created_at": None}]

		with patch("ai_ticket_platform.database.CRUD.ticket.Ticket") as mock_ticket_class:
			mock_ticket = MagicMock()
			mock_ticket_class.return_value = mock_ticket

			await create_tickets(db=mock_db, tickets_data=tickets_data)

			call_kwargs = mock_ticket_class.call_args[1]
			assert "created_at" not in call_kwargs
			assert call_kwargs["subject"] == "Test"
			assert call_kwargs["body"] == "Test body"

	async def test_create_tickets_database_error(self):
		"""Test handling of database errors during ticket creation."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add_all = MagicMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB Error"))
		mock_db.rollback = AsyncMock()

		tickets_data = [{"subject": "Test", "body": "Test body", "created_at": None}]

		with patch("ai_ticket_platform.database.CRUD.ticket.Ticket"):
			with pytest.raises(RuntimeError, match="Failed to create tickets"):
				await create_tickets(db=mock_db, tickets_data=tickets_data)

			mock_db.rollback.assert_called_once()

	async def test_create_tickets_empty_list(self):
		"""Test creating tickets with empty list."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add_all = MagicMock()
		mock_db.commit = AsyncMock()

		result = await create_tickets(db=mock_db, tickets_data=[])

		assert result == []
		mock_db.add_all.assert_called_once_with([])
		mock_db.commit.assert_called_once()


@pytest.mark.asyncio
class TestGetTicket:
	"""Test get_ticket by ID operation."""

	async def test_get_ticket_found(self):
		"""Test successful retrieval of ticket by ID."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_ticket = MagicMock()
		mock_ticket.id = 1
		mock_ticket.subject = "Test Ticket"

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=mock_ticket)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_ticket(db=mock_db, ticket_id=1)

		assert result == mock_ticket
		assert result.id == 1
		mock_db.execute.assert_called_once()

	async def test_get_ticket_not_found(self):
		"""Test ticket not found returns None."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=None)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_ticket(db=mock_db, ticket_id=999)

		assert result is None
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestListTickets:
	"""Test list_tickets with pagination."""

	async def test_list_tickets_default_pagination(self):
		"""Test listing tickets with default pagination."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_ticket_1 = MagicMock(id=1, subject="Ticket 1")
		mock_ticket_2 = MagicMock(id=2, subject="Ticket 2")

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_ticket_1, mock_ticket_2])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_tickets(db=mock_db)

		assert len(result) == 2
		assert result[0].id == 1
		assert result[1].id == 2
		mock_db.execute.assert_called_once()

	async def test_list_tickets_custom_pagination(self):
		"""Test listing tickets with custom skip and limit."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_tickets(db=mock_db, skip=10, limit=5)

		assert result == []
		mock_db.execute.assert_called_once()

	async def test_list_tickets_empty_database(self):
		"""Test listing tickets when database is empty."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_tickets(db=mock_db)

		assert result == []
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestCountTickets:
	"""Test count_tickets operation."""

	async def test_count_tickets_with_data(self):
		"""Test counting tickets when tickets exist."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one = MagicMock(return_value=42)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await count_tickets(db=mock_db)

		assert result == 42
		mock_db.execute.assert_called_once()

	async def test_count_tickets_empty_database(self):
		"""Test counting tickets when database is empty."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one = MagicMock(return_value=0)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await count_tickets(db=mock_db)

		assert result == 0
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestListTicketsByIntent:
	"""Test list_tickets_by_intent operation."""

	async def test_list_tickets_by_intent_found(self):
		"""Test listing tickets for specific intent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_ticket_1 = MagicMock(id=1, intent_id=5)
		mock_ticket_2 = MagicMock(id=2, intent_id=5)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_ticket_1, mock_ticket_2])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_tickets_by_intent(db=mock_db, intent_id=5)

		assert len(result) == 2
		assert result[0].intent_id == 5
		assert result[1].intent_id == 5
		mock_db.execute.assert_called_once()

	async def test_list_tickets_by_intent_no_tickets(self):
		"""Test listing tickets when intent has no tickets."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await list_tickets_by_intent(db=mock_db, intent_id=999)

		assert result == []
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestUpdateTicketIntent:
	"""Test update_ticket_intent operation."""

	async def test_update_ticket_intent_success(self):
		"""Test successfully updating ticket's intent_id."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_ticket = MagicMock()
		mock_ticket.id = 1
		mock_ticket.intent_id = None

		with patch("ai_ticket_platform.database.CRUD.ticket.get_ticket", new=AsyncMock(return_value=mock_ticket)):
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			result = await update_ticket_intent(db=mock_db, ticket_id=1, intent_id=10)

			assert result == mock_ticket
			assert result.intent_id == 10
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_ticket)

	async def test_update_ticket_intent_ticket_not_found(self):
		"""Test updating intent when ticket doesn't exist."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.database.CRUD.ticket.get_ticket", new=AsyncMock(return_value=None)):
			result = await update_ticket_intent(db=mock_db, ticket_id=999, intent_id=10)

			assert result is None
			# commit should not be called if ticket not found
			assert not hasattr(mock_db.commit, 'called') or not mock_db.commit.called

	async def test_update_ticket_intent_change_existing(self):
		"""Test updating ticket that already has an intent_id."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_ticket = MagicMock()
		mock_ticket.id = 1
		mock_ticket.intent_id = 5

		with patch("ai_ticket_platform.database.CRUD.ticket.get_ticket", new=AsyncMock(return_value=mock_ticket)):
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			result = await update_ticket_intent(db=mock_db, ticket_id=1, intent_id=15)

			assert result == mock_ticket
			assert result.intent_id == 15
			mock_db.commit.assert_called_once()


@pytest.mark.asyncio
class TestGetUnassignedTickets:
	"""Test get_unassigned_tickets operation."""

	async def test_get_unassigned_tickets_found(self):
		"""Test retrieving tickets without intent_id."""
		from ai_ticket_platform.database.CRUD.ticket import get_unassigned_tickets

		mock_db = MagicMock(spec=AsyncSession)
		mock_ticket_1 = MagicMock(id=1, intent_id=None)
		mock_ticket_2 = MagicMock(id=2, intent_id=None)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_ticket_1, mock_ticket_2])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_unassigned_tickets(db=mock_db)

		assert len(result) == 2
		assert result[0].intent_id is None
		assert result[1].intent_id is None
		mock_db.execute.assert_called_once()

	async def test_get_unassigned_tickets_empty(self):
		"""Test retrieving unassigned tickets when all are assigned."""
		from ai_ticket_platform.database.CRUD.ticket import get_unassigned_tickets

		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_unassigned_tickets(db=mock_db)

		assert result == []
		mock_db.execute.assert_called_once()
