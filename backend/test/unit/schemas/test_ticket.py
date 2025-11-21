"""Tests for Ticket schema validation"""
import pytest
from pydantic import ValidationError
from datetime import datetime
from ai_ticket_platform.schemas.endpoints.ticket import (
    TicketCreate, TicketUpdate, TicketResponse, CSVUploadResponse
)


class TestTicketCreate:
    """Test TicketCreate schema"""

    def test_valid_create(self):
        """Test valid ticket creation"""
        ticket = TicketCreate(subject="Test Subject", body="Test Body")
        assert ticket.subject == "Test Subject"
        assert ticket.body == "Test Body"

    def test_subject_required(self):
        """Test subject is required"""
        with pytest.raises(ValidationError):
            TicketCreate(body="Test Body")

    def test_body_required(self):
        """Test body is required"""
        with pytest.raises(ValidationError):
            TicketCreate(subject="Test Subject")

    def test_subject_empty_fails(self):
        """Test empty subject fails"""
        with pytest.raises(ValidationError):
            TicketCreate(subject="", body="Test Body")

    def test_subject_max_length(self):
        """Test subject max length"""
        with pytest.raises(ValidationError):
            TicketCreate(subject="x" * 501, body="Test Body")


class TestTicketUpdate:
    """Test TicketUpdate schema"""

    def test_intent_id_required(self):
        """Test intent_id is required"""
        with pytest.raises(ValidationError):
            TicketUpdate()

    def test_valid_intent_id(self):
        """Test valid intent_id"""
        update = TicketUpdate(intent_id=5)
        assert update.intent_id == 5

    def test_intent_id_must_be_int(self):
        """Test intent_id must be integer"""
        with pytest.raises(ValidationError):
            TicketUpdate(intent_id="5")
        with pytest.raises(ValidationError):
            TicketUpdate(intent_id=None)

    def test_intent_id_must_be_positive(self):
        """Test intent_id must be > 0"""
        with pytest.raises(ValidationError):
            TicketUpdate(intent_id=0)


class TestTicketResponse:
    """Test TicketResponse schema"""

    def test_valid_response(self):
        """Test valid response with all fields"""
        now = datetime.now()
        response = TicketResponse(
            id=1, subject="Test", body="Body",
            intent_id=5, created_at=now, updated_at=now
        )
        assert response.id == 1
        assert response.intent_id == 5

    def test_intent_id_optional(self):
        """Test intent_id is optional in response"""
        now = datetime.now()
        response = TicketResponse(
            id=1, subject="Test", body="Body",
            created_at=now, updated_at=now
        )
        assert response.intent_id is None


class TestCSVUploadResponse:
    """Test CSVUploadResponse schema"""

    def test_valid_response(self):
        """Test valid CSV upload response"""
        response = CSVUploadResponse(
            success=True,
            file_info={
                "filename": "test.csv",
                "rows_processed": 50,
                "rows_skipped": 0,
                "tickets_extracted": 50,
                "encoding": "utf-8"
            },
            tickets_created=50
        )
        assert response.success is True
        assert response.tickets_created == 50
        assert response.errors == []

    def test_success_required(self):
        """Test success is required"""
        with pytest.raises(ValidationError):
            CSVUploadResponse(file_info={}, tickets_created=0)

    def test_file_info_required(self):
        """Test file_info is required"""
        with pytest.raises(ValidationError):
            CSVUploadResponse(success=True, tickets_created=0)

    def test_tickets_created_non_negative(self):
        """Test tickets_created must be >= 0"""
        with pytest.raises(ValidationError):
            CSVUploadResponse(success=True, file_info={}, tickets_created=-1)