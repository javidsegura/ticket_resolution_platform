# S3 Setup Guide for Developers

## Part 1: Testing S3 Upload/Download (For You - Root User)

### Prerequisites
1. Ensure your AWS credentials are configured:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_MAIN_REGION`
   - `AWS_S3_BUCKET_NAME`

2. Start your backend server:
   ```bash
   cd backend
   # Activate venv if available
   source .venv/bin/activate  # or source venv/bin/activate
   python -m uvicorn ai_ticket_platform.main:app --reload
   ```

### Test Endpoints

The API will be available at `http://localhost:8000/api/s3-test`

#### 1. Check Bucket Configuration
```bash
curl http://localhost:8000/api/s3-test/bucket-info
```

#### 2. Test Upload (PUT presigned URL)

**Step 1:** Get a presigned URL for upload
```bash
curl "http://localhost:8000/api/s3-test/presigned-url/upload?file_path=test/myfile.jpg&content_type=image/jpeg"
```

**Step 2:** Upload a file using the returned presigned URL
```bash
# Replace <PRESIGNED_URL> with the URL from step 1
curl -X PUT \
  -H "Content-Type: image/jpeg" \
  --upload-file /path/to/your/file.jpg \
  "<PRESIGNED_URL>"
```

**Success Response:** Empty response with HTTP 200 status

#### 3. Test Download (GET presigned URL)

**Step 1:** Get a presigned URL for download
```bash
curl "http://localhost:8000/api/s3-test/presigned-url/download?file_path=test/myfile.jpg"
```

**Step 2:** Download the file using the returned presigned URL
```bash
# Replace <PRESIGNED_URL> with the URL from step 1
curl -o downloaded_file.jpg "<PRESIGNED_URL>"
```

Or simply paste the presigned URL in your browser!

### Verify in AWS Console

1. Go to AWS S3 Console
2. Find your bucket (name format: `{environment}-{project_name}-{random_string}`)
3. Check if your test file appears under `test/myfile.jpg`

---

## Part 2: Creating IAM Users for Developers (AWS Console)

Instead of giving developers your root credentials, create IAM users with limited S3 access.

### Step-by-Step Guide

#### 1. Navigate to IAM
1. Log in to AWS Console
2. Search for "IAM" in the search bar
3. Click on "IAM" service

#### 2. Create IAM Policy for S3 Access

1. In IAM dashboard, click **"Policies"** in the left sidebar
2. Click **"Create Policy"**
3. Click on the **"JSON"** tab
4. Paste the following policy (replace `YOUR_BUCKET_NAME` with your actual bucket name):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReadAndPut",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::YOUR_BUCKET_NAME",
        "arn:aws:s3:::YOUR_BUCKET_NAME/*"
      ]
    }
  ]
}
```

5. Click **"Next: Tags"** (optional - you can skip tags)
6. Click **"Next: Review"**
7. Name the policy: `S3-Upload-Download-Access-{YourProjectName}`
8. Add description: "Allows read and write access to project S3 bucket"
9. Click **"Create Policy"**

#### 3. Create IAM User for Each Developer

Repeat these steps for each developer:

1. In IAM dashboard, click **"Users"** in the left sidebar
2. Click **"Create user"**
3. Enter username (e.g., `dev-john-s3-access`)
4. Click **"Next"**

#### 4. Attach the Policy

1. Select **"Attach policies directly"**
2. Search for the policy you created: `S3-Upload-Download-Access-{YourProjectName}`
3. Check the box next to your policy
4. Click **"Next"**
5. Review and click **"Create user"**

#### 5. Create Access Keys

1. Click on the newly created user
2. Go to **"Security credentials"** tab
3. Scroll down to **"Access keys"** section
4. Click **"Create access key"**
5. Select **"Application running outside AWS"** (or "Other")
6. Click **"Next"**
7. (Optional) Add description tag
8. Click **"Create access key"**
9. **IMPORTANT:** Copy both:
   - Access key ID
   - Secret access key

   ⚠️ **Warning:** This is the ONLY time you'll see the secret access key!

10. Click **"Download .csv file"** to save the credentials
11. Click **"Done"**

#### 6. Share Credentials with Developer

**Send to each developer:**
- AWS Access Key ID: `AKIA...`
- AWS Secret Access Key: `...`
- AWS Region: (e.g., `us-east-1`)
- S3 Bucket Name: `{environment}-{project_name}-{random}`
- Instructions to set environment variables:

```bash
export AWS_ACCESS_KEY_ID="<their_access_key_id>"
export AWS_SECRET_ACCESS_KEY="<their_secret_access_key>"
export AWS_MAIN_REGION="<your_region>"
export AWS_S3_BUCKET_NAME="<your_bucket_name>"
```

Or for `.env` file:
```
AWS_ACCESS_KEY_ID=<their_access_key_id>
AWS_SECRET_ACCESS_KEY=<their_secret_access_key>
AWS_MAIN_REGION=<your_region>
AWS_S3_BUCKET_NAME=<your_bucket_name>
```

---

## Part 3: Developer Testing

Once developers have their credentials, they can test using the same endpoints:

```bash
# They should set their own credentials first
export AWS_ACCESS_KEY_ID="<their_key>"
export AWS_SECRET_ACCESS_KEY="<their_secret>"
export AWS_MAIN_REGION="us-east-1"
export AWS_S3_BUCKET_NAME="<bucket_name>"

# Start backend and test
cd backend
source .venv/bin/activate
python -m uvicorn ai_ticket_platform.main:app --reload

# Test in another terminal
curl "http://localhost:8000/api/s3-test/presigned-url/upload?file_path=dev-test/file.jpg&content_type=image/jpeg"
```

---

## Security Best Practices

1. **Rotate Keys Regularly:** Change access keys every 90 days
2. **Monitor Usage:** Check AWS CloudTrail for unusual activity
3. **Least Privilege:** Only grant the minimum required permissions
4. **Use Different Buckets:** Consider separate buckets for dev/staging/prod
5. **Enable MFA:** Require MFA for your root account
6. **Delete Old Keys:** Remove access keys for developers who leave the team

---

## Troubleshooting

### Error: "AccessDenied" or "not authorized to perform: s3:PutObject"

**This is the most common issue!** Use the debug script to check:

```bash
cd backend
./debug_iam_policy.sh Local-Devs-AI-Ticket-Platform your-bucket-name
```

This will show all policies, simulate permissions, and tell you exactly what's wrong.

**Quick Fix:**
```bash
cd backend
./fix_iam_policy.sh Local-Devs-AI-Ticket-Platform your-bucket-name
```

Choose option 1 (create new managed policy) - this is the cleanest approach.

**Common Causes:**
- Policy attached to wrong user
- Bucket name in policy doesn't match actual bucket (check the exact name!)
- Missing `/*` at the end of bucket ARN for object-level permissions
- Both resources needed: `arn:aws:s3:::BUCKET_NAME` AND `arn:aws:s3:::BUCKET_NAME/*`

### Error: "Invalid credentials"
- Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set correctly
- Check for extra spaces or quotes in environment variables

### Error: "Bucket not found"
- Verify AWS_S3_BUCKET_NAME is set correctly
- Check the bucket exists in the correct region

---

## Cleanup

To remove the test router after testing:

1. Remove import from `backend/src/ai_ticket_platform/routers/__init__.py`
2. Remove import from `backend/src/ai_ticket_platform/main.py`
3. Remove from routers list in both files
4. Delete `backend/src/ai_ticket_platform/routers/s3_test.py`
5. Delete this guide if no longer needed
