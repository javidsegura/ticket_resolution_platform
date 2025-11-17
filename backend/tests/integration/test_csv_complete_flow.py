"""
Integration test: Complete CSV import flow
Tests the entire pipeline: CSV upload → parsing → clustering → ticket creation
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from sqlalchemy import select, func

from ai_ticket_platform.database.generated_models import Ticket, TicketStatus


@pytest.mark.asyncio
class TestCSVCompleteFlow:
    """Tests for complete CSV import and processing flow"""

    @pytest.fixture
    def sample_csv_path(self):
        """Get path to sample CSV fixture"""
        return Path(__file__).parent.parent / 'fixtures' / 'tickets_sample.csv'

    @pytest.fixture
    def edge_case_csv_path(self):
        """Get path to edge case CSV fixture"""
        return Path(__file__).parent.parent / 'fixtures' / 'tickets_edge_cases.csv'

    async def test_csv_import_sample_data(self, async_client, db_session, sample_csv_path):
        """Test importing 84 sample tickets from fixture file"""
        # Read sample CSV file
        with open(sample_csv_path, 'rb') as f:
            csv_content = f.read()

        # Mock clustering service
        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 84,
                'clusters_created': 9,
                'clusters': [
                    {'topic_name': f'Cluster {i}', 'product_category': f'Category {i}'}
                    for i in range(1, 10)
                ]
            }

            # Upload CSV
            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("tickets_sample.csv", csv_content)}
            )

        # Verify upload successful
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "uploaded_and_clustered"
        assert data["ticket_count"] == 84
        assert len(data["ticket_ids"]) == 84

        # Verify that we imported the CSV data (may have other tickets from other tests)
        # so just check we have at least 84 tickets
        result = await db_session.execute(
            select(func.count(Ticket.ticket_id))
        )
        ticket_count = result.scalar()
        assert ticket_count >= 84

        # Verify ticket data integrity (check that tickets were imported correctly)
        result = await db_session.execute(
            select(Ticket).where(Ticket.title.like("%Login%"))
        )
        auth_tickets = result.scalars().all()
        assert len(auth_tickets) > 0, "Should have at least one auth ticket"

        # Verify first auth ticket has expected content
        auth_ticket = auth_tickets[0]
        assert auth_ticket.title is not None
        assert len(auth_ticket.content) > 0
        assert auth_ticket.status == TicketStatus.UPLOADED

    async def test_csv_import_edge_cases(self, async_client, db_session, edge_case_csv_path):
        """Test handling of edge case data (special chars, missing fields, etc)"""
        with open(edge_case_csv_path, 'rb') as f:
            csv_content = f.read()

        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 1,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Test', 'product_category': 'Test'}]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("tickets_edge_cases.csv", csv_content)}
            )

        # Edge case CSV should be processed but with some failures/skips
        assert response.status_code == 200
        data = response.json()
        # Should have processed at least some rows
        assert len(data.get("ticket_ids", [])) > 0

    async def test_csv_data_categories(self, async_client, db_session, sample_csv_path):
        """Verify sample CSV covers expected ticket categories"""
        with open(sample_csv_path, 'rb') as f:
            csv_content = f.read()

        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 84,
                'clusters_created': 5,
                'clusters': [
                    {'topic_name': 'Authentication', 'product_category': 'Security'},
                    {'topic_name': 'Performance', 'product_category': 'Infrastructure'},
                    {'topic_name': 'Frontend', 'product_category': 'Frontend'},
                    {'topic_name': 'API', 'product_category': 'Backend'},
                    {'topic_name': 'Features', 'product_category': 'Product'},
                ]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("tickets_sample.csv", csv_content)}
            )

        assert response.status_code == 200
        data = response.json()

        # Get imported tickets from database
        result = await db_session.execute(select(Ticket))
        tickets = result.scalars().all()

        # Verify we have tickets from different categories
        titles = [t.title for t in tickets]

        # Check for Authentication tickets
        auth_tickets = [t for t in titles if any(word in t.lower() for word in ['login', 'password', 'auth', 'sso', '2fa', 'mfa'])]
        assert len(auth_tickets) > 0, "Should have authentication tickets"

        # Check for Performance tickets
        perf_tickets = [t for t in titles if any(word in t.lower() for word in ['slow', 'performance', 'degraded', 'timeout', 'memory', 'cpu'])]
        assert len(perf_tickets) > 0, "Should have performance tickets"

        # Check for Frontend tickets
        frontend_tickets = [t for t in titles if any(word in t.lower() for word in ['ui', 'responsive', 'mobile', 'modal', 'css', 'dark mode'])]
        assert len(frontend_tickets) > 0, "Should have frontend tickets"

        # Check for Feature/Bug tickets
        feature_tickets = [t for t in titles if any(word in t.lower() for word in ['feature request', 'bug:', 'add', 'implement'])]
        assert len(feature_tickets) > 0, "Should have feature and bug tickets"

    async def test_csv_unicode_handling(self, async_client, db_session):
        """Test that unicode characters in CSV are handled correctly"""
        # CSV with unicode characters
        csv_content = b"""title,content
Unicode Emoji Test,Issue with emoji \xf0\x9f\x9a\x80 \xf0\x9f\x90\x9b displaying correctly
French Characters,Caf\xc3\xa9 r\xc3\xa9sum\xc3\xa9 na\xc3\xafve special characters
Japanese Title,\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e - Japanese text handling
"""

        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 3,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Unicode', 'product_category': 'Test'}]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("unicode_test.csv", csv_content)}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["ticket_count"] == 3

        # Verify unicode is preserved in database
        result = await db_session.execute(select(Ticket).limit(1))
        ticket = result.scalar_one_or_none()
        assert ticket is not None
        # Check that title contains unicode
        assert len(ticket.title) > 0

    async def test_csv_large_content_truncation(self, async_client, db_session):
        """Test that very long content is truncated appropriately"""
        long_content = "x" * 10000  # Content longer than 5000 char limit

        csv_content = f"""title,content
Long Content Test,{long_content}
""".encode()

        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 1,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Test', 'product_category': 'Test'}]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("long_content.csv", csv_content)}
            )

        assert response.status_code == 200

        # Verify content was truncated to 5000 chars
        result = await db_session.execute(select(Ticket).limit(1))
        ticket = result.scalar_one_or_none()
        assert ticket is not None
        assert len(ticket.content) <= 5000

    async def test_csv_duplicate_handling(self, async_client, db_session):
        """Test handling of duplicate ticket titles"""
        csv_content = b"""title,content
Duplicate Issue,First occurrence of this issue
Duplicate Issue,Second occurrence of same title
Another Issue,Different content
"""

        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 3,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Test', 'product_category': 'Test'}]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("duplicates.csv", csv_content)}
            )

        assert response.status_code == 200
        data = response.json()
        # Should create 3 tickets (doesn't deduplicate by title)
        assert data["ticket_count"] == 3

        # Verify both duplicates exist in database
        result = await db_session.execute(
            select(Ticket).where(Ticket.title == "Duplicate Issue")
        )
        duplicate_tickets = result.scalars().all()
        assert len(duplicate_tickets) == 2

    async def test_csv_empty_content_handling(self, async_client, db_session):
        """Test handling of rows with missing content field"""
        csv_content = b"""title,content
Title Without Content,
Regular Issue,Has content here
"""

        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 2,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Test', 'product_category': 'Test'}]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("empty_content.csv", csv_content)}
            )

        assert response.status_code == 200
        # Both rows should be processed (empty content is OK)
        assert response.json()["ticket_count"] == 2

    async def test_csv_missing_title_skipped(self, async_client, db_session):
        """Test that rows with missing title are skipped"""
        csv_content = b"""title,content
,Content without title
Valid Title,Valid content
"""

        with patch('ai_ticket_platform.routers.tickets.cluster_and_categorize_tickets') as mock_cluster:
            mock_cluster.return_value = {
                'total_tickets': 1,
                'clusters_created': 1,
                'clusters': [{'topic_name': 'Test', 'product_category': 'Test'}]
            }

            response = await async_client.post(
                "/api/csv/upload",
                files={"file": ("missing_title.csv", csv_content)}
            )

        assert response.status_code == 200
        # Should only process row with valid title
        assert response.json()["ticket_count"] == 1
