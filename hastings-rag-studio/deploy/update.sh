#!/usr/bin/env bash
# =============================================================================
# Hastings RAG Studio — Redeploy (update existing deployment)
# Run this whenever you push new code changes to production.
# =============================================================================

set -euo pipefail

AWS_ACCOUNT="${AWS_ACCOUNT:-$(aws sts get-caller-identity --query Account --output text)}"
AWS_REGION="${AWS_REGION:-us-east-1}"
APP_NAME="hastings-rag-studio"
ECR_URI="${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com/${APP_NAME}"
IMAGE_TAG="latest"

echo "▶ Rebuilding and pushing Docker image…"
aws ecr get-login-password --region "${AWS_REGION}" | \
    docker login --username AWS --password-stdin "${AWS_ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -t "${APP_NAME}:${IMAGE_TAG}" .
docker tag "${APP_NAME}:${IMAGE_TAG}" "${ECR_URI}:${IMAGE_TAG}"
docker push "${ECR_URI}:${IMAGE_TAG}"
echo "  ✅ Image pushed"

echo "▶ Triggering App Runner redeployment…"
SERVICE_ARN=$(aws apprunner list-services \
    --region "${AWS_REGION}" \
    --query "ServiceSummaryList[?ServiceName=='${APP_NAME}'].ServiceArn" \
    --output text)

aws apprunner start-deployment \
    --service-arn "${SERVICE_ARN}" \
    --region "${AWS_REGION}"

echo "  ✅ Redeployment triggered"
echo "  Monitor at: https://console.aws.amazon.com/apprunner/home?region=${AWS_REGION}"
