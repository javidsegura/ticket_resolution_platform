"""
CSV Upload and Ticket Management Router
Handles ticket creation, clustering, and draft generation
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
import csv
from io import StringIO

from ai_ticket_platform.database.generated_models import Ticket, TicketStatus
from ai_ticket_platform.dependencies.database import get_db
from ai_ticket_platform.dependencies.settings import get_app_settings
from ai_ticket_platform.core.clients.llm import LLMClient
from ai_ticket_platform.services.clustering.cluster_service import cluster_and_categorize_tickets

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tickets"])


@router.post("/csv/upload", response_model=dict)
async def upload_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    settings = Depends(get_app_settings)
):
    """
    Upload a CSV file, create tickets, and perform clustering.

    Args:
        file: CSV file to upload (expects columns: title, content)
        db: Database session
        settings: Application settings with LLM configuration

    Returns:
        dict with ticket IDs and clustering results
    """
    try:
        # Read and decode file
        content = await file.read()
        csv_text = content.decode('utf-8')

        # Parse CSV
        csv_reader = csv.DictReader(StringIO(csv_text))
        rows = list(csv_reader)

        if not rows:
            raise ValueError("CSV file is empty")

        # Create Ticket records
        tickets = []
        ticket_ids = []

        for row in rows:
            title = row.get('title', '').strip()
            content = row.get('content', '').strip()

            if not title:
                logger.warning("Skipping row with empty title")
                continue

            ticket = Ticket(
                title=title,
                content=content[:5000],  # Max 5000 chars
                status=TicketStatus.UPLOADED
            )
            db.add(ticket)
            tickets.append(ticket)
            ticket_ids.append(ticket.title)  # Store title for clustering

        await db.commit()

        # Refresh to get IDs
        for ticket in tickets:
            await db.refresh(ticket)

        logger.info(f"Created {len(tickets)} tickets from CSV upload")

        # Perform clustering using LLM service
        try:
            llm_client = LLMClient(settings)

            # Prepare tickets for clustering (expects "Ticket Subject" field)
            clustering_input = [
                {"Ticket Subject": ticket.title}
                for ticket in tickets
            ]

            clustering_result = cluster_and_categorize_tickets(clustering_input, llm_client)

            logger.info(f"Clustering complete: {clustering_result.get('clusters_created', 0)} clusters created")

            return {
                "ticket_count": len(tickets),
                "ticket_ids": [ticket.ticket_id for ticket in tickets],
                "status": "uploaded_and_clustered",
                "clustering": clustering_result
            }
        except Exception as clustering_error:
            logger.error(f"Clustering failed: {str(clustering_error)}")
            # Don't fail the upload if clustering fails - tickets are already created
            return {
                "ticket_count": len(tickets),
                "ticket_ids": [ticket.ticket_id for ticket in tickets],
                "status": "uploaded",
                "clustering_error": str(clustering_error)
            }

    except Exception as e:
        logger.error(f"Error uploading CSV: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to upload CSV: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/cluster", response_model=dict)
async def cluster_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    settings = Depends(get_app_settings)
):
    """
    Cluster a ticket into categories using LLM service.

    Args:
        ticket_id: ID of the ticket to cluster
        db: Database session
        settings: Application settings with LLM configuration

    Returns:
        dict with clusters and primary cluster
    """
    # Verify ticket exists
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )

    try:
        # Initialize LLM client and perform clustering
        llm_client = LLMClient(settings)

        clustering_input = [{"Ticket Subject": ticket.title}]
        clustering_result = cluster_and_categorize_tickets(clustering_input, llm_client)

        logger.info(f"Clustered ticket {ticket_id}")

        return {
            "ticket_id": ticket_id,
            "total_tickets": clustering_result.get("total_tickets", 0),
            "clusters_created": clustering_result.get("clusters_created", 0),
            "clusters": clustering_result.get("clusters", []),
            "primary_cluster": clustering_result.get("clusters", [{}])[0].get("topic_name") if clustering_result.get("clusters") else None
        }
    except Exception as e:
        logger.error(f"Error clustering ticket {ticket_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Clustering failed: {str(e)}"
        )


@router.post("/tickets/{ticket_id}/status", response_model=dict)
async def update_ticket_status(
    ticket_id: str,
    new_status: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Update ticket status.

    Args:
        ticket_id: ID of the ticket
        new_status: New status (UPLOADED, PROCESSING, DRAFT_READY)
        db: Database session

    Returns:
        Updated ticket with new status
    """
    # Verify status is valid
    valid_statuses = [status.value for status in TicketStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )

    ticket.status = new_status
    await db.commit()
    await db.refresh(ticket)

    logger.info(f"Updated ticket {ticket_id} status to {new_status}")

    return {
        "ticket_id": ticket.ticket_id,
        "status": ticket.status,
        "title": ticket.title
    }


@router.get("/tickets/{ticket_id}", response_model=dict)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a ticket by ID.

    Args:
        ticket_id: ID of the ticket
        db: Database session

    Returns:
        Ticket details
    """
    result = await db.execute(select(Ticket).where(Ticket.ticket_id == ticket_id))
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} not found"
        )

    return {
        "ticket_id": ticket.ticket_id,
        "title": ticket.title,
        "content": ticket.content,
        "status": ticket.status,
        "created_at": ticket.created_at.isoformat(),
        "updated_at": ticket.updated_at.isoformat()
    }
