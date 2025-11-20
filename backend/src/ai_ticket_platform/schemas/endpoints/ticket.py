from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TicketBase(BaseModel):
    """Base ticket schema with common fields"""
    subject: str = Field(..., min_length=1, max_length=500, description="Ticket subject/title")
    body: str = Field(..., description="Ticket description/body")

class TicketCreate(TicketBase):
    """Schema for creating a ticket"""
    pass

# Clustering will update intent_id from None to corresponding (not optional anymore)
class TicketUpdate(BaseModel):
    """Schema for updating a ticket"""
    intent_id: int = Field(..., description="Linked intent ID")
    
# Response after intent_id assigned
class TicketResponse(TicketBase):
    """Schema for ticket responses"""
    id: int = Field(..., description="Ticket ID")
    intent_id: int = Field(..., description="Linked intent ID")
    created_at: datetime = Field(..., description="Ticket creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    model_config = {"from_attributes": True}

class TicketListResponse(BaseModel):
    """Schema for paginated ticket list"""
    total: int = Field(..., ge=0, description="Total tickets count")
    skip: int = Field(..., ge=0, description="Number skipped")
    limit: int = Field(..., ge=1, description="Limit applied")
    tickets: list[TicketResponse] = Field(..., description="List of tickets")

# file_info, tickets_created, errors in csv_parser.py, router receives result and passes it to CSVUploadResponse
class CSVUploadResponse(BaseModel):
    """Schema for CSV upload response"""
    success: bool = Field(..., description="Whether upload succeeded")
    file_info: dict = Field(..., description="File metadata (filename, rows_processed, etc)")
    tickets_created: int = Field(..., ge=0, description="Number of tickets created in DB")
    errors: list[str] = Field(default_factory=list, description="Any parsing errors encountered")