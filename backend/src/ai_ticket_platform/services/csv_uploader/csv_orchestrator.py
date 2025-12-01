import logging
import tempfile
import os
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file
from ai_ticket_platform.services.csv_uploader.csv_uploader import save_tickets_to_db, cluster_tickets_with_cache

logger = logging.getLogger(__name__)


async def upload_csv_file(file: UploadFile, db: AsyncSession) -> dict:
    """
    Orchestrates the CSV upload workflow and returns a summary of processing results.
    
    Parameters:
        file (UploadFile): The uploaded CSV file to process.
        db (AsyncSession): Database session used to persist parsed tickets.
    
    Returns:
        dict: Summary of the upload containing:
            - success (bool): True when processing completed without unhandled errors.
            - file_info (dict): Metadata about the uploaded file and parse results.
            - tickets_created (int): Number of tickets saved to the database.
            - clustering (dict):
                - clusters_created (int): Number of clusters created during clustering.
                - total_tickets_clustered (int): Total tickets considered for clustering.
            - errors (list): Any validation or parsing errors encountered.
    
    Raises:
        ValueError: If the CSV content is invalid or fails validation during parsing.
    """
    
    tmp_path = None
    
    try:
        logger.info(f"Processing CSV upload: {file.filename}")
        
        # Save uploaded file temporarily (stream in chunks to avoid high memory usage)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                tmp.write(chunk)
            tmp_path = tmp.name
        
        logger.debug(f"Saved temp file to: {tmp_path}")
        
        # Parse CSV
        csv_result = parse_csv_file(tmp_path)
        logger.info(f"Parsed CSV: {csv_result['file_info']['tickets_extracted']} tickets extracted")

        # Cluster tickets with caching (hash-based deduplication)
        clustering_result = await cluster_tickets_with_cache(csv_result["tickets"])
        logger.info(f"Clustering completed: {clustering_result.get('clusters_created', 0)} clusters")

        # Save to database
        tickets = await save_tickets_to_db(db, csv_result["tickets"])
        logger.info(f"Saved {len(tickets)} tickets to database")

        # Response
        return {
            "success": True,
            "file_info": csv_result["file_info"],
            "tickets_created": len(tickets),
            "clustering": {
                "clusters_created": clustering_result.get("clusters_created", 0),
                "total_tickets_clustered": clustering_result.get("total_tickets", 0)
            },
            "errors": csv_result.get("errors", [])
        }
    
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise  # Re-raise for router to handle
    
    except Exception as e:
        logger.error(f"Error during CSV upload: {str(e)}")
        raise  # Re-raise for router to handle
    
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug(f"Cleaned up temp file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {tmp_path}: {str(e)}")