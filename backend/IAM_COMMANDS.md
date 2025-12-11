# IAM Policy Debug & Fix - Quick Reference

## Your Current Issue

```
User: arn:aws:iam::233047281012:user/Local-Devs-AI-Ticket-Platform
Bucket: ai-ticket-platform-remote-state-bucket-zxmluk37
Error: User is not authorized to perform: s3:PutObject
```

---

## 🔍 Step 1: Debug (Check What's Wrong)

```bash
cd backend
./debug_iam_policy.sh \
  Local-Devs-AI-Ticket-Platform \
  ai-ticket-platform-remote-state-bucket-zxmluk37
```

This will show you:
- ✓ All policies attached to the user
- ✓ Policy documents (JSON)
- ✓ Simulation results for s3:PutObject and s3:GetObject
- ✓ Exact recommendations

---

## 🔧 Step 2: Fix (Add/Update Policy)

### Option A: Automated Fix (Recommended)

```bash
cd backend
./fix_iam_policy.sh \
  Local-Devs-AI-Ticket-Platform \
  ai-ticket-platform-remote-state-bucket-zxmluk37
```

Then choose **Option 1** (Create new managed policy).

### Option B: Manual Fix (AWS CLI)

```bash
# Create the policy JSON
cat > /tmp/s3-dev-policy.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ai-ticket-platform-remote-state-bucket-zxmluk37",
        "arn:aws:s3:::ai-ticket-platform-remote-state-bucket-zxmluk37/*"
      ]
    }
  ]
}
EOF

# Create the policy
aws iam create-policy \
  --policy-name S3-Dev-Access-Fix \
  --policy-document file:///tmp/s3-dev-policy.json

# Get your account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Attach to user
aws iam attach-user-policy \
  --user-name Local-Devs-AI-Ticket-Platform \
  --policy-arn arn:aws:iam::${ACCOUNT_ID}:policy/S3-Dev-Access-Fix
```

### Option C: AWS Console Fix

1. Go to: https://console.aws.amazon.com/iam/
2. Click **Policies** → **Create Policy**
3. Switch to **JSON** tab
4. Paste:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::ai-ticket-platform-remote-state-bucket-zxmluk37",
        "arn:aws:s3:::ai-ticket-platform-remote-state-bucket-zxmluk37/*"
      ]
    }
  ]
}
```
5. Click **Next** → Name it `S3-Dev-Access-Fix`
6. Click **Create Policy**
7. Go to **Users** → `Local-Devs-AI-Ticket-Platform`
8. Click **Permissions** tab → **Add permissions** → **Attach policies**
9. Search for `S3-Dev-Access-Fix` and attach it

---

## ✅ Step 3: Verify

```bash
# Test with AWS CLI (using the dev's credentials)
aws s3 ls s3://ai-ticket-platform-remote-state-bucket-zxmluk37/

# Test upload
echo "test" > test.txt
aws s3 cp test.txt s3://ai-ticket-platform-remote-state-bucket-zxmluk37/test.txt

# Test download
aws s3 cp s3://ai-ticket-platform-remote-state-bucket-zxmluk37/test.txt downloaded.txt
```

If these work, your app should work too!

---

## 📝 To Answer Your Original Question

### "Can I modify the IAM policy later?"

**YES! Absolutely!** You have 3 ways to modify policies:

### 1. Edit Existing Policy (AWS Console)
- IAM → Policies → Click your policy → Edit
- Make changes → Save
- Changes apply immediately to all attached users

### 2. Update Policy via CLI
```bash
# Create new version of existing policy
aws iam create-policy-version \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/YOUR_POLICY_NAME \
  --policy-document file:///tmp/updated-policy.json \
  --set-as-default
```

### 3. Replace Policy
- Detach old policy from user
- Create new policy
- Attach new policy to user

**Note:** Managed policies can have up to 5 versions. Delete old ones if you hit the limit:
```bash
aws iam delete-policy-version \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/YOUR_POLICY \
  --version-id v1
```

---

## Common Mistakes & Fixes

| Problem | Cause | Fix |
|---------|-------|-----|
| Still getting AccessDenied | Wrong bucket name in policy | Check exact bucket name with `aws s3 ls` |
| Policy attached but not working | Missing `/*` in Resource | Add both `bucket` and `bucket/*` to Resources |
| Can list but not upload | Only bucket-level permission | Add `arn:aws:s3:::BUCKET/*` to Resources |
| Works in CLI but not in app | App using different credentials | Check `AWS_ACCESS_KEY_ID` in app env vars |

---

## Need Help?

1. Run debug script first: `./debug_iam_policy.sh`
2. Check the simulation results
3. If still stuck, share the output of debug script
