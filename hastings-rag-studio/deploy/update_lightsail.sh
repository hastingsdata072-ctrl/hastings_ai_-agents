#!/usr/bin/env bash
# =============================================================================
# Hastings RAG Studio — Redeploy to Lightsail (push code updates)
# =============================================================================

set -euo pipefail

AWS_REGION="us-east-1"
INSTANCE_NAME="hastings-rag-studio"
APP_DIR="/home/ubuntu/hastings-rag-studio"

PUBLIC_IP=$(aws lightsail get-instance \
    --instance-name "${INSTANCE_NAME}" \
    --region "${AWS_REGION}" \
    --query 'instance.publicIpAddress' \
    --output text)

echo "▶ Syncing files to ${PUBLIC_IP}…"
rsync -avz \
    --exclude 'venv/' \
    --exclude '.env' \
    --exclude 'assets/uploads/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    -e "ssh -i ~/.ssh/hastings-rag-key.pem -o StrictHostKeyChecking=no" \
    ./ "ubuntu@${PUBLIC_IP}:${APP_DIR}/"

echo "▶ Rebuilding and restarting app…"
ssh -i ~/.ssh/hastings-rag-key.pem -o StrictHostKeyChecking=no \
    ubuntu@${PUBLIC_IP} \
    "cd ${APP_DIR} && sudo docker compose up -d --build app"

echo "✅ Update complete. App at http://${PUBLIC_IP}:8501"
