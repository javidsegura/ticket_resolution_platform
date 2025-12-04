#!/usr/bin/env python3
"""
Script to verify article blobs in Azure Blob Storage.
Downloads and displays the content of an article blob to verify presigned URL implementation.

Run inside the backend container where dependencies are available:
docker exec deployment-backend python /app/verify_article_blob.py
"""

import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def verify_article_blob():
    """Fetch an article from DB and download its blob content."""

    # Database connection
    db_url = (
        f"{os.getenv('MYSQL_ASYNC_DRIVER', 'mysql+aiomysql')}://"
        f"{os.getenv('MYSQL_USER', 'root')}:"
        f"{os.getenv('MYSQL_PASSWORD', 'rootpassword')}@"
        f"{os.getenv('MYSQL_HOST', 'localhost')}:"
        f"{os.getenv('MYSQL_PORT', '3306')}/"
        f"{os.getenv('MYSQL_DATABASE', 'ai_ticket_platform')}"
    )

    print(f"[INFO] Connecting to database...")
    engine = create_async_engine(db_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with AsyncSessionLocal() as session:
            # Get one article blob_path
            result = await session.execute(
                text("SELECT id, blob_path, type FROM articles LIMIT 1")
            )
            row = result.fetchone()

            if not row:
                print("[ERROR] No articles found in database")
                return

            article_id, blob_path, article_type = row
            print(f"\n[INFO] Found article:")
            print(f"  ID: {article_id}")
            print(f"  Type: {article_type}")
            print(f"  Blob Path: {blob_path}")

            # Import Azure storage client (synchronous)
            try:
                from azure.storage.blob import BlobClient
            except ImportError:
                print("[ERROR] Azure SDK not available. Install: pip install azure-storage-blob")
                return

            # Get Azure credentials from environment
            account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
            account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
            container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME')

            if not all([account_name, account_key, container_name]):
                print("[ERROR] Azure credentials not found in environment")
                print(f"  AZURE_STORAGE_ACCOUNT_NAME: {account_name}")
                print(f"  AZURE_STORAGE_ACCOUNT_KEY: {'***' if account_key else 'NOT SET'}")
                print(f"  AZURE_STORAGE_CONTAINER_NAME: {container_name}")
                return

            # Construct blob URL and client
            blob_url = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_path}"

            print(f"\n[INFO] Downloading from Azure Blob Storage:")
            print(f"  Account: {account_name}")
            print(f"  Container: {container_name}")
            print(f"  Blob URL: {blob_url}")

            try:
                # Create blob client with account key (synchronous)
                blob_client = BlobClient(
                    account_url=f"https://{account_name}.blob.core.windows.net",
                    container_name=container_name,
                    blob_name=blob_path,
                    credential=account_key
                )

                # Download blob content
                print(f"\n[INFO] Downloading blob content...")
                download_stream = blob_client.download_blob()
                content = download_stream.readall()

                # Decode and display
                text_content = content.decode('utf-8')
                print(f"\n[SUCCESS] Blob downloaded successfully! Content length: {len(text_content)} bytes")
                print(f"\n{'='*80}")
                print(f"ARTICLE CONTENT (ID: {article_id}, Type: {article_type}):")
                print(f"{'='*80}\n")
                print(text_content)
                print(f"\n{'='*80}")
                print(f"[SUCCESS] Article blob verification complete!")

            except Exception as e:
                print(f"[ERROR] Failed to download blob: {e}")
                import traceback
                traceback.print_exc()

    except Exception as e:
        print(f"[ERROR] Database error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(verify_article_blob())
