#!/bin/bash

# Quick fix script to add S3 permissions to an IAM user

set -e

USER_NAME="${1:-Local-Devs-AI-Ticket-Platform}"
BUCKET_NAME="${2:-ai-ticket-platform-remote-state-bucket-zxmluk37}"
POLICY_NAME="S3-Dev-Access-${BUCKET_NAME}-Fix"

echo "=========================================="
echo "IAM Policy Fix Script"
echo "=========================================="
echo "User: $USER_NAME"
echo "Bucket: $BUCKET_NAME"
echo "Policy Name: $POLICY_NAME"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create policy document
POLICY_DOC=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3DevAccess",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${BUCKET_NAME}",
        "arn:aws:s3:::${BUCKET_NAME}/*"
      ]
    }
  ]
}
EOF
)

echo "Policy Document:"
echo "$POLICY_DOC" | python3 -m json.tool
echo ""

# Save to temp file
TEMP_POLICY_FILE=$(mktemp)
echo "$POLICY_DOC" > "$TEMP_POLICY_FILE"

echo -e "${YELLOW}Choose an option:${NC}"
echo "1. Create NEW managed policy and attach to user (recommended)"
echo "2. Add as INLINE policy to user (quick & dirty)"
echo "3. UPDATE existing managed policy (if you already have one)"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo -e "${YELLOW}Creating new managed policy...${NC}"

        # Get account ID
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
        POLICY_ARN="arn:aws:iam::${ACCOUNT_ID}:policy/${POLICY_NAME}"

        # Create policy
        if aws iam create-policy \
            --policy-name "$POLICY_NAME" \
            --policy-document "file://${TEMP_POLICY_FILE}" \
            --description "S3 access for developers on bucket ${BUCKET_NAME}" 2>/dev/null; then
            echo -e "${GREEN}✓ Policy created: $POLICY_ARN${NC}"
        else
            echo -e "${RED}Policy already exists or creation failed. Trying to get existing policy ARN...${NC}"
        fi

        # Attach to user
        echo ""
        echo -e "${YELLOW}Attaching policy to user...${NC}"
        if aws iam attach-user-policy \
            --user-name "$USER_NAME" \
            --policy-arn "$POLICY_ARN"; then
            echo -e "${GREEN}✓ Policy attached to user${NC}"
        else
            echo -e "${RED}✗ Failed to attach policy${NC}"
            exit 1
        fi
        ;;

    2)
        echo ""
        echo -e "${YELLOW}Adding inline policy to user...${NC}"
        if aws iam put-user-policy \
            --user-name "$USER_NAME" \
            --policy-name "S3AccessInline" \
            --policy-document "file://${TEMP_POLICY_FILE}"; then
            echo -e "${GREEN}✓ Inline policy added${NC}"
        else
            echo -e "${RED}✗ Failed to add inline policy${NC}"
            exit 1
        fi
        ;;

    3)
        echo ""
        read -p "Enter the ARN of the existing policy to update: " EXISTING_POLICY_ARN

        echo -e "${YELLOW}Creating new policy version...${NC}"
        if aws iam create-policy-version \
            --policy-arn "$EXISTING_POLICY_ARN" \
            --policy-document "file://${TEMP_POLICY_FILE}" \
            --set-as-default; then
            echo -e "${GREEN}✓ Policy updated${NC}"
        else
            echo -e "${RED}✗ Failed to update policy${NC}"
            echo "Note: You may have reached the version limit (5 versions max)."
            echo "Delete old versions first with:"
            echo "aws iam delete-policy-version --policy-arn $EXISTING_POLICY_ARN --version-id v1"
            exit 1
        fi
        ;;

    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Cleanup
rm -f "$TEMP_POLICY_FILE"

echo ""
echo "=========================================="
echo -e "${GREEN}✓ IAM Policy Fixed!${NC}"
echo "=========================================="
echo ""
echo "The user should now have access to:"
echo "  - s3:GetObject"
echo "  - s3:PutObject"
echo "  - s3:DeleteObject"
echo "  - s3:ListBucket"
echo ""
echo "On bucket: $BUCKET_NAME"
echo ""
echo "Test with:"
echo "  aws s3 ls s3://${BUCKET_NAME}/"
echo "  echo 'test' > test.txt && aws s3 cp test.txt s3://${BUCKET_NAME}/test.txt"
echo ""
