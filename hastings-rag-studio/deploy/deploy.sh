#!/usr/bin/env bash
# =============================================================================
# Hastings RAG Studio — Full AWS Deployment Script
# Region: us-east-1
# Account: 755370915486
#
# Run this script once to provision all AWS infrastructure and deploy the app.
# Safe to re-run — all steps are idempotent.
#
# Prerequisites:
#   - AWS CLI v2 configured (aws sts get-caller-identity must work)
#   - Docker installed and running
#   - You are in the project root: hastings-rag-studio/
# =============================================================================

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
AWS_ACCOUNT="755370915486"
AWS_REGION="us-east-1"
APP_NAME="hastings-rag-studio"
ECR_REPO="${APP_NAME}"
IMAGE_TAG="latest"
ECR_URI="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

DB_INSTANCE="hastings-rag-db"
DB_NAME="hastings_rag"
DB_USER="hastings_admin"
DB_PASSWORD="$(openssl rand -base64 24 | tr -dc 'A-Za-z0-9' | head -c 24)"

S3_BUCKET="${APP_NAME}-documents-${AWS_ACCOUNT}"
SECRET_NAME="${APP_NAME}/production"
APPRUNNER_SERVICE="${APP_NAME}"

echo "================================================================"
echo "  Hastings RAG Studio — AWS Deployment"
echo "  Account: ${AWS_ACCOUNT} | Region: ${AWS_REGION}"
echo "================================================================"
echo ""

# ── Step 1: ECR Repository ────────────────────────────────────────────────────
echo "▶ Step 1/7: Creating ECR repository…"
aws ecr describe-repositories --repository-names "${ECR_REPO}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 || \
aws ecr create-repository \
    --repository-name "${ECR_REPO}" \
    --region "${AWS_REGION}" \
    --image-scanning-configuration scanOnPush=true \
    --output table
echo "  ✅ ECR repository: ${ECR_URI}"

# ── Step 2: Build and push Docker image ───────────────────────────────────────
echo ""
echo "▶ Step 2/7: Building and pushing Docker image…"
aws ecr get-login-password --region "${AWS_REGION}" | \
    docker login --username AWS --password-stdin "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -t "${ECR_REPO}:${IMAGE_TAG}" .
docker tag "${ECR_REPO}:${IMAGE_TAG}" "${ECR_URI}:${IMAGE_TAG}"
docker push "${ECR_URI}:${IMAGE_TAG}"
echo "  ✅ Image pushed: ${ECR_URI}:${IMAGE_TAG}"

# ── Step 3: S3 Bucket ─────────────────────────────────────────────────────────
echo ""
echo "▶ Step 3/7: Creating S3 bucket…"
aws s3api head-bucket --bucket "${S3_BUCKET}" 2>/dev/null || \
aws s3api create-bucket \
    --bucket "${S3_BUCKET}" \
    --region "${AWS_REGION}" \
    --create-bucket-configuration LocationConstraint="${AWS_REGION}" 2>/dev/null || \
aws s3api create-bucket \
    --bucket "${S3_BUCKET}" \
    --region "${AWS_REGION}"

# Block all public access
aws s3api put-public-access-block \
    --bucket "${S3_BUCKET}" \
    --public-access-block-configuration \
    "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
echo "  ✅ S3 bucket: s3://${S3_BUCKET}"

# ── Step 4: RDS PostgreSQL ────────────────────────────────────────────────────
echo ""
echo "▶ Step 4/7: Creating RDS PostgreSQL instance…"
echo "  (This takes 5–10 minutes — please wait)"

# Check if already exists
DB_STATUS=$(aws rds describe-db-instances \
    --db-instance-identifier "${DB_INSTANCE}" \
    --region "${AWS_REGION}" \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>/dev/null || echo "not-found")

if [ "${DB_STATUS}" = "not-found" ] || [ "${DB_STATUS}" = "None" ]; then
    aws rds create-db-instance \
        --db-instance-identifier "${DB_INSTANCE}" \
        --db-instance-class db.t4g.micro \
        --engine postgres \
        --engine-version "16.3" \
        --master-username "${DB_USER}" \
        --master-user-password "${DB_PASSWORD}" \
        --db-name "${DB_NAME}" \
        --allocated-storage 20 \
        --storage-type gp2 \
        --no-multi-az \
        --publicly-accessible \
        --backup-retention-period 1 \
        --no-deletion-protection \
        --region "${AWS_REGION}" \
        --output table

    echo "  ⏳ Waiting for RDS to become available (5–10 min)…"
    aws rds wait db-instance-available \
        --db-instance-identifier "${DB_INSTANCE}" \
        --region "${AWS_REGION}"
else
    echo "  ℹ️  RDS instance already exists (status: ${DB_STATUS})"
fi

# Get RDS endpoint
DB_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "${DB_INSTANCE}" \
    --region "${AWS_REGION}" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)
echo "  ✅ RDS endpoint: ${DB_ENDPOINT}"

# ── Step 5: Secrets Manager ───────────────────────────────────────────────────
echo ""
echo "▶ Step 5/7: Storing secrets in Secrets Manager…"

# Read GROQ_API_KEY from local .env
GROQ_API_KEY=$(grep GROQ_API_KEY /mnt/c/Users/user/Downloads/Hastings\ studion/hastings-rag-studio/.env | cut -d'=' -f2)
GROQ_MODEL=$(grep GROQ_MODEL /mnt/c/Users/user/Downloads/Hastings\ studion/hastings-rag-studio/.env | cut -d'=' -f2)

DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_ENDPOINT}:5432/${DB_NAME}"

SECRET_VALUE=$(cat <<EOF
{
  "GROQ_API_KEY": "${GROQ_API_KEY}",
  "GROQ_MODEL": "${GROQ_MODEL}",
  "DATABASE_URL": "${DATABASE_URL}",
  "EMBEDDING_MODEL": "all-MiniLM-L6-v2",
  "CHUNK_SIZE": "1000",
  "CHUNK_OVERLAP": "150",
  "TOP_K": "5",
  "S3_BUCKET": "${S3_BUCKET}"
}
EOF
)

aws secretsmanager describe-secret --secret-id "${SECRET_NAME}" \
    --region "${AWS_REGION}" > /dev/null 2>&1 && \
aws secretsmanager update-secret \
    --secret-id "${SECRET_NAME}" \
    --secret-string "${SECRET_VALUE}" \
    --region "${AWS_REGION}" || \
aws secretsmanager create-secret \
    --name "${SECRET_NAME}" \
    --description "Hastings RAG Studio production secrets" \
    --secret-string "${SECRET_VALUE}" \
    --region "${AWS_REGION}"

echo "  ✅ Secrets stored: ${SECRET_NAME}"

# Save DB password locally for reference
echo "DB_PASSWORD=${DB_PASSWORD}" >> /tmp/hastings_deploy_info.txt
echo "DB_ENDPOINT=${DB_ENDPOINT}" >> /tmp/hastings_deploy_info.txt
echo "DATABASE_URL=${DATABASE_URL}" >> /tmp/hastings_deploy_info.txt

# ── Step 6: IAM Role for App Runner ──────────────────────────────────────────
echo ""
echo "▶ Step 6/7: Creating IAM role for App Runner…"

ROLE_NAME="${APP_NAME}-apprunner-role"
TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "tasks.apprunner.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}'

aws iam get-role --role-name "${ROLE_NAME}" > /dev/null 2>&1 || \
aws iam create-role \
    --role-name "${ROLE_NAME}" \
    --assume-role-policy-document "${TRUST_POLICY}"

# Allow reading secrets and S3
POLICY="{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {
      \"Effect\": \"Allow\",
      \"Action\": [\"secretsmanager:GetSecretValue\"],
      \"Resource\": \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}*\"
    },
    {
      \"Effect\": \"Allow\",
      \"Action\": [\"s3:GetObject\",\"s3:PutObject\",\"s3:DeleteObject\",\"s3:ListBucket\"],
      \"Resource\": [
        \"arn:aws:s3:::${S3_BUCKET}\",
        \"arn:aws:s3:::${S3_BUCKET}/*\"
      ]
    },
    {
      \"Effect\": \"Allow\",
      \"Action\": [\"logs:CreateLogGroup\",\"logs:CreateLogStream\",\"logs:PutLogEvents\"],
      \"Resource\": \"*\"
    }
  ]
}"

aws iam put-role-policy \
    --role-name "${ROLE_NAME}" \
    --policy-name "${APP_NAME}-policy" \
    --policy-document "${POLICY}"

ROLE_ARN=$(aws iam get-role --role-name "${ROLE_NAME}" \
    --query 'Role.Arn' --output text)
echo "  ✅ IAM role: ${ROLE_ARN}"

# ── Step 7: App Runner ────────────────────────────────────────────────────────
echo ""
echo "▶ Step 7/7: Deploying to App Runner…"

# ECR access role
ECR_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT}:role/AppRunnerECRAccessRole"

# Check if ECR access role exists
aws iam get-role --role-name "AppRunnerECRAccessRole" > /dev/null 2>&1 || {
    ECR_TRUST='{
      "Version":"2012-10-17",
      "Statement":[{
        "Effect":"Allow",
        "Principal":{"Service":"build.apprunner.amazonaws.com"},
        "Action":"sts:AssumeRole"
      }]
    }'
    aws iam create-role \
        --role-name "AppRunnerECRAccessRole" \
        --assume-role-policy-document "${ECR_TRUST}"
    aws iam attach-role-policy \
        --role-name "AppRunnerECRAccessRole" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# Check if service already exists
SERVICE_ARN=$(aws apprunner list-services \
    --region "${AWS_REGION}" \
    --query "ServiceSummaryList[?ServiceName=='${APPRUNNER_SERVICE}'].ServiceArn" \
    --output text 2>/dev/null || echo "")

if [ -z "${SERVICE_ARN}" ]; then
    SERVICE_ARN=$(aws apprunner create-service \
        --service-name "${APPRUNNER_SERVICE}" \
        --region "${AWS_REGION}" \
        --source-configuration "{
          \"ImageRepository\": {
            \"ImageIdentifier\": \"${ECR_URI}:${IMAGE_TAG}\",
            \"ImageConfiguration\": {
              \"Port\": \"8501\",
              \"RuntimeEnvironmentSecrets\": {
                \"GROQ_API_KEY\":        \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}:GROQ_API_KEY::\",
                \"GROQ_MODEL\":          \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}:GROQ_MODEL::\",
                \"DATABASE_URL\":        \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}:DATABASE_URL::\",
                \"EMBEDDING_MODEL\":     \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}:EMBEDDING_MODEL::\",
                \"CHUNK_SIZE\":          \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}:CHUNK_SIZE::\",
                \"CHUNK_OVERLAP\":       \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}:CHUNK_OVERLAP::\",
                \"TOP_K\":              \"arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT}:secret:${SECRET_NAME}:TOP_K::\"
              }
            },
            \"ImageRepositoryType\": \"ECR\"
          },
          \"AuthenticationConfiguration\": {
            \"AccessRoleArn\": \"${ECR_ROLE_ARN}\"
          }
        }" \
        --instance-configuration "{
          \"Cpu\": \"0.25 vCPU\",
          \"Memory\": \"0.5 GB\",
          \"InstanceRoleArn\": \"${ROLE_ARN}\"
        }" \
        --health-check-configuration "{
          \"Protocol\": \"HTTP\",
          \"Path\": \"/_stcore/health\",
          \"Interval\": 10,
          \"Timeout\": 5,
          \"HealthyThreshold\": 1,
          \"UnhealthyThreshold\": 5
        }" \
        --query 'Service.ServiceArn' \
        --output text)
    echo "  ⏳ Waiting for App Runner to deploy (3–5 min)…"
    aws apprunner wait service-running \
        --service-arn "${SERVICE_ARN}" \
        --region "${AWS_REGION}" 2>/dev/null || true
else
    echo "  ℹ️  App Runner service already exists — triggering redeployment…"
    aws apprunner start-deployment \
        --service-arn "${SERVICE_ARN}" \
        --region "${AWS_REGION}"
fi

# Get the service URL
SERVICE_URL=$(aws apprunner describe-service \
    --service-arn "${SERVICE_ARN}" \
    --region "${AWS_REGION}" \
    --query 'Service.ServiceUrl' \
    --output text)

echo ""
echo "================================================================"
echo "  ✅ Deployment complete!"
echo "================================================================"
echo ""
echo "  App URL:      https://${SERVICE_URL}"
echo "  RDS endpoint: ${DB_ENDPOINT}"
echo "  S3 bucket:    s3://${S3_BUCKET}"
echo "  Secret:       ${SECRET_NAME}"
echo ""
echo "  Next step: initialise the production database"
echo "  Run: psql \${DATABASE_URL} -f deploy/init_prod_db.sql"
echo ""
echo "  Deployment info saved to: /tmp/hastings_deploy_info.txt"
echo "================================================================"
