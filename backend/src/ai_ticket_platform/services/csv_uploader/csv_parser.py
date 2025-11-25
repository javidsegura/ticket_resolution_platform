import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

def parse_csv_file(file_path: str) -> Dict:
    """
    Parse a CSV file of tickets and return structured ticket records with parsing metadata.
    
    Expects CSV to contain at least the columns `subject` and `body`. Rows with empty `subject` or `body` are skipped. If a `created_at` value is present it is parsed as an ISO-formatted date/time; rows with invalid `created_at` are skipped and an error entry is recorded. The function also detects the file encoding before reading.
    
    Returns:
        dict: A result dictionary with keys:
            - `success` (bool): Always True on successful return.
            - `file_info` (dict): Metadata including:
                - `filename` (str): The input file name.
                - `rows_processed` (int): Number of CSV data rows read.
                - `rows_skipped` (int): Number of rows skipped due to validation (empty subject/body or invalid created_at).
                - `tickets_extracted` (int): Number of tickets parsed and returned.
                - `encoding` (str): Detected file encoding.
            - `tickets` (list): List of ticket dicts. Each ticket contains:
                - `subject` (str)
                - `source_row` (int): Original CSV row number (1-based header + data rows).
                - `id` (str|None)
                - `created_at` (datetime|None)
                - `body` (str)
            - `errors` (list): List of error messages encountered while parsing rows.
    
    Raises:
        FileNotFoundError: If the given file path does not exist.
        ValueError: If required columns (`subject`, `body`) are missing or no valid tickets are found.
        RuntimeError: If an unexpected error occurs while reading or parsing the CSV file.
    """
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    filename = file_path.name
    logger.info(f"Starting CSV parsing for file: {filename}")
    
    # Detect encoding
    encoding = _detect_encoding(file_path)
    logger.debug(f"Detected encoding: {encoding}")
    
    tickets = []
    errors = []
    rows_processed = 0
    rows_skipped = 0
    
    try:
        with open(file_path, 'r', encoding=encoding) as csvfile:
            reader = csv.DictReader(csvfile)

            # Validate required columns exist
            required_columns = ['subject', 'body']
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or invalid")

            missing_columns = [col for col in required_columns if col not in reader.fieldnames]
            if missing_columns:
                raise ValueError(
                    f"CSV must contain {required_columns} columns. "
                    f"Missing: {missing_columns}. "
                    f"Found columns: {reader.fieldnames}"
                )

            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                rows_processed += 1

                try:
                    subject = row.get('subject', '').strip()
                    body = row.get('body', '').strip()

                    # Skip rows with empty subject or body
                    if not subject or not body:
                        rows_skipped += 1
                        reason = "empty subject" if not subject else "empty body"
                        logger.debug(f"Skipping row {row_num}: {reason}")
                        continue

                    # Parse created_at if present, otherwise None to allow database default
                    created_at_val = None
                    if created_at_str := row.get('created_at'):
                        try:
                            # Handle YYYY-MM-DD or YYYY-MM-DD HH:MM:SS formats
                            created_at_val = datetime.fromisoformat(created_at_str.strip())
                        except (ValueError, TypeError):
                            errors.append(f"Error parsing 'created_at' on row {row_num}: '{created_at_str}'")
                            continue

                    # Create ticket dict for clustering
                    ticket = {
                        "subject": subject,
                        "source_row": row_num,
                        "id": row.get('id'),
                        "created_at": created_at_val,
                        "body": body,
                    }

                    tickets.append(ticket)
                    
                except Exception as e:
                    error_msg = f"Error parsing row {row_num}: {str(e)}"
                    logger.warning(error_msg)
                    errors.append(error_msg)
    
    except ValueError as e:
        logger.error(f"Validation error in CSV: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        raise RuntimeError(f"Failed to parse CSV: {str(e)}") from e
    
    if not tickets:
        raise ValueError(
            f"No valid tickets found in CSV. "
            f"Processed {rows_processed} rows, skipped {rows_skipped}."
        )
    
    logger.info(
        f"Successfully parsed CSV: {len(tickets)} tickets extracted, "
        f"{rows_skipped} rows skipped"
    )
    
    return {
        "success": True,
        "file_info": {
            "filename": filename,
            "rows_processed": rows_processed,
            "rows_skipped": rows_skipped,
            "tickets_extracted": len(tickets),
            "encoding": encoding
        },
        "tickets": tickets,
        "errors": errors
    }


def _detect_encoding(file_path: Path) -> str:
    """
    Detect file encoding by trying common encodings.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        Detected encoding string
    """
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                f.read(1024)  # Try reading first 1KB
            logger.debug(f"Successfully detected encoding: {encoding}")
            return encoding
        except (UnicodeDecodeError, LookupError):
            continue
    
    # Default to utf-8 if all fail
    logger.warning("Could not detect encoding, defaulting to utf-8")
    return 'utf-8'

