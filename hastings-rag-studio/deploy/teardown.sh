#!/usr/bin/env bash
# =============================================================================
# Hastings RAG Studio — Teardown (delete all AWS resources)
# WARNING: This deletes everything including the database. Irreversible.
# =============================================================================

set -euo pipefail

AWS_ACCOUNT="755370915486"
AWS_REGION="us-east-1"
APP_NAME="hastings-rag-studio"
DB_INSTANCE="hastings-rag-db"
S3_BUCKET="${APP_NAME}-documents-${AWS_ACCOUNT}"
SECRET_NAME="${APP_NAME}/production"

echo "⚠️  This will DELETE all AWS resources for Hastings RAG Studio."
echo "    Account: ${AWS_ACCOUNT} | Region: ${AWS_REGION}"
read -p "Type 'yes' to confirm: " CONFIRM
[ "${CONFIRM}" = "yes" ] || { echo "Aborted."; exit 1; }

echo "▶ Deleting App Runner service…"
SERVICE_ARN=$(aws apprunner list-services \
    --region "${AWS_REGION}" \
    --query "ServiceSummaryList[?ServiceName=='${APP_NAME}'].ServiceArn" \
    --output text 2>/dev/null || echo "")
[ -n "${SERVICE_ARN}" ] && aws apprunner delete-service \
    --service-arn "${SERVICE_ARN}" --region "${AWS_REGION}" || true

echo "▶ Deleting RDS instance (this takes several minutes)…"
aws rds delete-db-instance \
    --db-instance-identifier "${DB_INSTANCE}" \
    --skip-final-snapshot \
    --delete-automated-backups \
    --region "${AWS_REGION}" 2>/dev/null || true

echo "▶ Emptying and deleting S3 bucket…"
aws s3 rm "s3://${S3_BUCKET}" --recursive 2>/dev/null || true
aws s3api delete-bucket --bucket "${S3_BUCKET}" --region "${AWS_REGION}" 2>/dev/null || true

echo "▶ Deleting secret…"
aws secretsmanager delete-secret \
    --secret-id "${SECRET_NAME}" \
    --force-delete-without-recovery \
    --region "${AWS_REGION}" 2>/dev/null || true

echo "▶ Deleting ECR repository…"
aws ecr delete-repository \
    --repository-name "${APP_NAME}" \
    --force \
    --region "${AWS_REGION}" 2>/dev/null || true

echo "✅ Teardown complete."
