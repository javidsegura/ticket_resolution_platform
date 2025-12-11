#!/bin/bash

# S3 Operations Test Script
# This script tests the S3 presigned URL endpoints

set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8000/api/s3-test}"
TEST_FILE="${TEST_FILE:-test_upload.txt}"
TEST_S3_PATH="${TEST_S3_PATH:-test/upload_$(date +%s).txt}"

echo "=========================================="
echo "S3 Presigned URL Test Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check bucket info
echo -e "${YELLOW}Step 1: Checking S3 bucket configuration...${NC}"
BUCKET_INFO=$(curl -s "${API_BASE_URL}/bucket-info")
echo "$BUCKET_INFO" | python3 -m json.tool
BUCKET_NAME=$(echo "$BUCKET_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['bucket_name'])")
echo -e "${GREEN}✓ Bucket configured: $BUCKET_NAME${NC}"
echo ""

# Step 2: Create test file if it doesn't exist
if [ ! -f "$TEST_FILE" ]; then
    echo -e "${YELLOW}Creating test file: $TEST_FILE${NC}"
    echo "This is a test file created at $(date)" > "$TEST_FILE"
    echo "Testing S3 upload with presigned URL" >> "$TEST_FILE"
    echo -e "${GREEN}✓ Test file created${NC}"
fi
echo ""

# Step 3: Get upload presigned URL
echo -e "${YELLOW}Step 2: Getting presigned URL for upload...${NC}"
UPLOAD_RESPONSE=$(curl -s "${API_BASE_URL}/presigned-url/upload?file_path=${TEST_S3_PATH}&content_type=text/plain")
echo "$UPLOAD_RESPONSE" | python3 -m json.tool
UPLOAD_URL=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['presigned_url'])")
echo -e "${GREEN}✓ Presigned upload URL obtained${NC}"
echo ""

# Step 4: Upload file
echo -e "${YELLOW}Step 3: Uploading file to S3...${NC}"
UPLOAD_HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
    -H "Content-Type: text/plain" \
    --upload-file "$TEST_FILE" \
    "$UPLOAD_URL")

if [ "$UPLOAD_HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ File uploaded successfully (HTTP $UPLOAD_HTTP_CODE)${NC}"
else
    echo -e "${RED}✗ Upload failed (HTTP $UPLOAD_HTTP_CODE)${NC}"
    exit 1
fi
echo ""

# Step 5: Wait a moment for S3 consistency
echo -e "${YELLOW}Waiting for S3 consistency...${NC}"
sleep 2
echo ""

# Step 6: Get download presigned URL
echo -e "${YELLOW}Step 4: Getting presigned URL for download...${NC}"
DOWNLOAD_RESPONSE=$(curl -s "${API_BASE_URL}/presigned-url/download?file_path=${TEST_S3_PATH}")
echo "$DOWNLOAD_RESPONSE" | python3 -m json.tool
DOWNLOAD_URL=$(echo "$DOWNLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['presigned_url'])")
echo -e "${GREEN}✓ Presigned download URL obtained${NC}"
echo ""

# Step 7: Download file
echo -e "${YELLOW}Step 5: Downloading file from S3...${NC}"
DOWNLOADED_FILE="downloaded_${TEST_FILE}"
curl -s -o "$DOWNLOADED_FILE" "$DOWNLOAD_URL"
echo -e "${GREEN}✓ File downloaded to: $DOWNLOADED_FILE${NC}"
echo ""

# Step 8: Verify content
echo -e "${YELLOW}Step 6: Verifying file content...${NC}"
echo "Original file content:"
cat "$TEST_FILE"
echo ""
echo "Downloaded file content:"
cat "$DOWNLOADED_FILE"
echo ""

if diff "$TEST_FILE" "$DOWNLOADED_FILE" > /dev/null; then
    echo -e "${GREEN}✓ File content matches! Upload/Download test PASSED${NC}"
else
    echo -e "${RED}✗ File content mismatch! Test FAILED${NC}"
    exit 1
fi
echo ""

# Cleanup
echo -e "${YELLOW}Cleaning up local test files...${NC}"
rm -f "$DOWNLOADED_FILE"
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

echo "=========================================="
echo -e "${GREEN}All tests PASSED!${NC}"
echo "=========================================="
echo ""
echo "File uploaded to S3: s3://${BUCKET_NAME}/${TEST_S3_PATH}"
echo ""
echo "You can verify in AWS Console:"
echo "  https://s3.console.aws.amazon.com/s3/buckets/${BUCKET_NAME}?prefix=${TEST_S3_PATH}"
