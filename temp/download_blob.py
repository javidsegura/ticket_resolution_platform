import sys
sys.path.insert(0, '/Users/fc/Documents/AAASEM/DevOps/RAGDevOps/ticket_resolution_platform/backend/src')

from ai_ticket_platform.services.infra.storage.azure import AzureBlobStorage
from ai_ticket_platform.database.main import initialize_db_engine
from sqlalchemy import text
import asyncio

async def main():
    # Get database connection
    AsyncSessionLocal = initialize_db_engine()
    
    async with AsyncSessionLocal() as db:
        # Query one article's blob path
        result = await db.execute(text("SELECT blob_path FROM articles LIMIT 1"))
        row = result.fetchone()
        
        if not row:
            print("No articles found!")
            return
        
        blob_path = row[0]
        print(f"Downloading blob: {blob_path}\n")
        
        # Download from Azure
        storage = AzureBlobStorage("images")
        content = storage.download_blob(blob_path)
        
        print("=" * 80)
        print("BLOB CONTENT:")
        print("=" * 80)
        print(content)
        print("=" * 80)

asyncio.run(main())
EOF