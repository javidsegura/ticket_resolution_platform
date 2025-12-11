#!/bin/bash

# IAM Policy Debug Script
# Checks the policies attached to an IAM user and verifies S3 permissions

set -e

USER_NAME="${1:-Local-Devs-AI-Ticket-Platform}"
BUCKET_NAME="${2:-ai-ticket-platform-remote-state-bucket-zxmluk37}"

echo "=========================================="
echo "IAM Policy Debugger"
echo "=========================================="
echo "User: $USER_NAME"
echo "Bucket: $BUCKET_NAME"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Check if user exists
echo -e "${YELLOW}Step 1: Checking if user exists...${NC}"
if aws iam get-user --user-name "$USER_NAME" &>/dev/null; then
    echo -e "${GREEN}✓ User exists${NC}"
else
    echo -e "${RED}✗ User does not exist!${NC}"
    exit 1
fi
echo ""

# Step 2: List attached managed policies
echo -e "${YELLOW}Step 2: Listing attached managed policies...${NC}"
MANAGED_POLICIES=$(aws iam list-attached-user-policies --user-name "$USER_NAME" --output json)
echo "$MANAGED_POLICIES" | python3 -m json.tool

POLICY_ARNS=$(echo "$MANAGED_POLICIES" | python3 -c "import sys, json; policies = json.load(sys.stdin).get('AttachedPolicies', []); print('\n'.join([p['PolicyArn'] for p in policies]))" || echo "")

if [ -z "$POLICY_ARNS" ]; then
    echo -e "${RED}✗ No managed policies attached!${NC}"
else
    echo -e "${GREEN}✓ Found managed policies${NC}"
fi
echo ""

# Step 3: Get policy details for each managed policy
if [ -n "$POLICY_ARNS" ]; then
    echo -e "${YELLOW}Step 3: Getting policy details...${NC}"
    while IFS= read -r policy_arn; do
        if [ -n "$policy_arn" ]; then
            echo -e "${BLUE}Policy ARN: $policy_arn${NC}"

            # Get default version
            DEFAULT_VERSION=$(aws iam get-policy --policy-arn "$policy_arn" --query 'Policy.DefaultVersionId' --output text)
            echo "Default Version: $DEFAULT_VERSION"

            # Get policy document
            echo "Policy Document:"
            aws iam get-policy-version --policy-arn "$policy_arn" --version-id "$DEFAULT_VERSION" --query 'PolicyVersion.Document' --output json | python3 -m json.tool
            echo ""
        fi
    done <<< "$POLICY_ARNS"
fi

# Step 4: List inline policies
echo -e "${YELLOW}Step 4: Checking inline policies...${NC}"
INLINE_POLICIES=$(aws iam list-user-policies --user-name "$USER_NAME" --output json)
echo "$INLINE_POLICIES" | python3 -m json.tool

INLINE_POLICY_NAMES=$(echo "$INLINE_POLICIES" | python3 -c "import sys, json; print('\n'.join(json.load(sys.stdin).get('PolicyNames', [])))" || echo "")

if [ -z "$INLINE_POLICY_NAMES" ]; then
    echo -e "${YELLOW}No inline policies found${NC}"
else
    echo -e "${GREEN}✓ Found inline policies${NC}"

    # Get inline policy documents
    while IFS= read -r policy_name; do
        if [ -n "$policy_name" ]; then
            echo -e "${BLUE}Inline Policy: $policy_name${NC}"
            aws iam get-user-policy --user-name "$USER_NAME" --policy-name "$policy_name" --query 'PolicyDocument' --output json | python3 -m json.tool
            echo ""
        fi
    done <<< "$INLINE_POLICY_NAMES"
fi
echo ""

# Step 5: Simulate policy for specific S3 actions
echo -e "${YELLOW}Step 5: Simulating S3 PutObject policy...${NC}"
USER_ARN=$(aws iam get-user --user-name "$USER_NAME" --query 'User.Arn' --output text)
echo "User ARN: $USER_ARN"
echo ""

echo "Testing s3:PutObject on $BUCKET_NAME..."
SIMULATE_PUT=$(aws iam simulate-principal-policy \
    --policy-source-arn "$USER_ARN" \
    --action-names "s3:PutObject" \
    --resource-arns "arn:aws:s3:::${BUCKET_NAME}/*" \
    --output json)

echo "$SIMULATE_PUT" | python3 -m json.tool

PUT_DECISION=$(echo "$SIMULATE_PUT" | python3 -c "import sys, json; print(json.load(sys.stdin)['EvaluationResults'][0]['EvalDecision'])")

if [ "$PUT_DECISION" = "allowed" ]; then
    echo -e "${GREEN}✓ s3:PutObject is ALLOWED${NC}"
else
    echo -e "${RED}✗ s3:PutObject is DENIED${NC}"
fi
echo ""

echo "Testing s3:GetObject on $BUCKET_NAME..."
SIMULATE_GET=$(aws iam simulate-principal-policy \
    --policy-source-arn "$USER_ARN" \
    --action-names "s3:GetObject" \
    --resource-arns "arn:aws:s3:::${BUCKET_NAME}/*" \
    --output json)

GET_DECISION=$(echo "$SIMULATE_GET" | python3 -c "import sys, json; print(json.load(sys.stdin)['EvaluationResults'][0]['EvalDecision'])")

if [ "$GET_DECISION" = "allowed" ]; then
    echo -e "${GREEN}✓ s3:GetObject is ALLOWED${NC}"
else
    echo -e "${RED}✗ s3:GetObject is DENIED${NC}"
fi
echo ""

# Step 6: Summary and recommendations
echo "=========================================="
echo -e "${BLUE}SUMMARY & RECOMMENDATIONS${NC}"
echo "=========================================="
echo ""

if [ "$PUT_DECISION" = "allowed" ] && [ "$GET_DECISION" = "allowed" ]; then
    echo -e "${GREEN}✓ User has correct S3 permissions!${NC}"
else
    echo -e "${RED}✗ User is missing S3 permissions!${NC}"
    echo ""
    echo "Required policy (paste in AWS Console → IAM → Policies → Create/Edit):"
    echo ""
    cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
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
    echo ""
    echo "To fix via CLI:"
    echo ""
    echo "# Option 1: Create and attach a new managed policy"
    echo "cat > /tmp/s3-policy.json <<'POLICY_EOF'"
    echo "{"
    echo '  "Version": "2012-10-17",'
    echo '  "Statement": ['
    echo '    {'
    echo '      "Effect": "Allow",'
    echo '      "Action": ["s3:GetObject", "s3:PutObject", "s3:ListBucket"],'
    echo "      \"Resource\": [\"arn:aws:s3:::${BUCKET_NAME}\", \"arn:aws:s3:::${BUCKET_NAME}/*\"]"
    echo '    }'
    echo '  ]'
    echo "}"
    echo "POLICY_EOF"
    echo ""
    echo "aws iam create-policy --policy-name S3-Dev-Access-Fix --policy-document file:///tmp/s3-policy.json"
    echo "aws iam attach-user-policy --user-name $USER_NAME --policy-arn arn:aws:iam::\$(aws sts get-caller-identity --query Account --output text):policy/S3-Dev-Access-Fix"
    echo ""
    echo "# Option 2: Add inline policy (quick & dirty)"
    echo "aws iam put-user-policy --user-name $USER_NAME --policy-name S3AccessInline --policy-document file:///tmp/s3-policy.json"
fi

echo ""
echo "=========================================="
