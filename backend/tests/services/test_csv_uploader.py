import os
from ai_ticket_platform.services.csv_uploader.csv_parser import parse_csv_file

def test_parse_csv_file():
    # Path to a sample CSV file for testing
    csv_path = os.path.join(os.path.dirname(__file__), "tickets.csv")
    result = parse_csv_file(csv_path)
    print(result)
    assert result["success"] is True
    assert "file_info" in result
    assert isinstance(result["tickets"], list)
    # Optionally, add more assertions based on expected ticket data
    
    
#run: pytest -s tests/services/test_csv_uploader.py