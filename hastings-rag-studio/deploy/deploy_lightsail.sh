#!/usr/bin/env bash
# =============================================================================
# Hastings RAG Studio — AWS Lightsail Deployment
# Cost: ~$7/month (Lightsail 2GB instance)
#
# What this does:
#   1. Creates a Lightsail instance (Ubuntu 22.04)
#   2. Installs Docker + pgvector PostgreSQL on the instance
#   3. Copies the app and runs it as a Docker container
#   4. Opens port 8501 for web access
#
# Prerequisites:
#   - AWS CLI v2 configured
#   - Run from project root: hastings-rag-studio/
# =============================================================================

set -euo pipefail

AWS_REGION="us-east-1"
INSTANCE_NAME="hastings-rag-studio"
BUNDLE_ID="nano_3_0"          # 2 vCPU, 512MB RAM — $7/month
BLUEPRINT_ID="ubuntu_22_04"
KEY_NAME="hastings-rag-key"
APP_DIR="/home/ubuntu/hastings-rag-studio"
DB_PASSWORD="$(openssl rand -base64 16 | tr -dc 'A-Za-z0-9' | head -c 20)"

echo "================================================================"
echo "  Hastings RAG Studio — Lightsail Deployment"
echo "  Region: ${AWS_REGION}"
echo "================================================================"
echo ""

# ── Step 1: Create SSH key pair ───────────────────────────────────────────────
echo "▶ Step 1/5: Creating SSH key pair…"
if ! aws lightsail get-key-pair --key-pair-name "${KEY_NAME}" \
        --region "${AWS_REGION}" > /dev/null 2>&1; then
    aws lightsail create-key-pair \
        --key-pair-name "${KEY_NAME}" \
        --region "${AWS_REGION}" \
        --query 'privateKeyBase64' \
        --output text | base64 -d > ~/.ssh/hastings-rag-key.pem
    chmod 600 ~/.ssh/hastings-rag-key.pem
    echo "  ✅ SSH key saved to ~/.ssh/hastings-rag-key.pem"
else
    echo "  ℹ️  Key pair already exists"
    # Check if local key exists
    [ -f ~/.ssh/hastings-rag-key.pem ] || {
        echo "  ⚠️  Key pair exists in AWS but local .pem not found."
        echo "  Delete the key pair in Lightsail console and re-run, or"
        echo "  place your existing .pem at ~/.ssh/hastings-rag-key.pem"
        exit 1
    }
fi

# ── Step 2: Create Lightsail instance ─────────────────────────────────────────
echo ""
echo "▶ Step 2/5: Creating Lightsail instance…"
if ! aws lightsail get-instance --instance-name "${INSTANCE_NAME}" \
        --region "${AWS_REGION}" > /dev/null 2>&1; then

    # Build the startup script that runs on first boot
    STARTUP_SCRIPT=$(cat <<'STARTUP'
#!/bin/bash
apt-get update -qq
apt-get install -y -qq docker.io docker-compose-plugin
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu
# Install pgvector PostgreSQL
docker pull pgvector/pgvector:pg16
STARTUP
)

    aws lightsail create-instances \
        --instance-names "${INSTANCE_NAME}" \
        --availability-zone "${AWS_REGION}a" \
        --blueprint-id "${BLUEPRINT_ID}" \
        --bundle-id "${BUNDLE_ID}" \
        --key-pair-name "${KEY_NAME}" \
        --user-data "${STARTUP_SCRIPT}" \
        --region "${AWS_REGION}"

    echo "  ⏳ Waiting for instance to start (2–3 min)…"
    sleep 30
    # Poll until running
    for i in {1..20}; do
        STATE=$(aws lightsail get-instance \
            --instance-name "${INSTANCE_NAME}" \
            --region "${AWS_REGION}" \
            --query 'instance.state.name' \
            --output text)
        echo "    Status: ${STATE}"
        [ "${STATE}" = "running" ] && break
        sleep 15
    done
else
    echo "  ℹ️  Instance already exists"
fi

# Get public IP
PUBLIC_IP=$(aws lightsail get-instance \
    --instance-name "${INSTANCE_NAME}" \
    --region "${AWS_REGION}" \
    --query 'instance.publicIpAddress' \
    --output text)
echo "  ✅ Instance IP: ${PUBLIC_IP}"

# ── Step 3: Open firewall ports ───────────────────────────────────────────────
echo ""
echo "▶ Step 3/5: Opening firewall ports…"
aws lightsail put-instance-public-ports \
    --instance-name "${INSTANCE_NAME}" \
    --region "${AWS_REGION}" \
    --port-infos \
        '[{"fromPort":22,"toPort":22,"protocol":"tcp"},
          {"fromPort":8501,"toPort":8501,"protocol":"tcp"},
          {"fromPort":80,"toPort":80,"protocol":"tcp"}]' > /dev/null
echo "  ✅ Ports 22, 80, 8501 open"

# ── Step 4: Copy app files to instance ───────────────────────────────────────
echo ""
echo "▶ Step 4/5: Copying app to instance…"
echo "  ⏳ Waiting for SSH to be ready…"
sleep 30

SSH_CMD="ssh -i ~/.ssh/hastings-rag-key.pem -o StrictHostKeyChecking=no ubuntu@${PUBLIC_IP}"

# Wait for SSH
for i in {1..15}; do
    $SSH_CMD "echo ok" > /dev/null 2>&1 && break || sleep 10
done

# Create app directory
$SSH_CMD "mkdir -p ${APP_DIR}"

# Copy project files (exclude venv and uploads)
rsync -avz \
    --exclude 'venv/' \
    --exclude '.env' \
    --exclude 'assets/uploads/' \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    -e "ssh -i ~/.ssh/hastings-rag-key.pem -o StrictHostKeyChecking=no" \
    ./ "ubuntu@${PUBLIC_IP}:${APP_DIR}/"

echo "  ✅ Files copied"

# ── Step 5: Start services on instance ───────────────────────────────────────
echo ""
echo "▶ Step 5/5: Starting services on instance…"

# Read local .env values
GROQ_API_KEY=$(grep GROQ_API_KEY .env | cut -d'=' -f2)
GROQ_MODEL=$(grep GROQ_MODEL .env | cut -d'=' -f2)

# Create .env on the server
$SSH_CMD "cat > ${APP_DIR}/.env << 'ENVEOF'
GROQ_API_KEY=${GROQ_API_KEY}
GROQ_MODEL=${GROQ_MODEL}
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@localhost:5432/hastings_rag
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
TOP_K=5
ENVEOF"

# Create docker-compose.yml on server
$SSH_CMD "cat > ${APP_DIR}/docker-compose.yml << 'COMPOSEEOF'
version: '3.8'
services:
  db:
    image: pgvector/pgvector:pg16
    container_name: hastings-pg
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: hastings_rag
    volumes:
      - pgdata:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: [\"CMD-SHELL\", \"pg_isready -U postgres\"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    container_name: hastings-app
    ports:
      - \"8501:8501\"
      - \"80:8501\"
    env_file: .env
    environment:
      DATABASE_URL: postgresql://postgres:${DB_PASSWORD}@db:5432/hastings_rag
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

volumes:
  pgdata:
COMPOSEEOF"

# Install docker compose plugin and start everything
$SSH_CMD "cd ${APP_DIR} && sudo docker compose up -d --build"

echo "  ⏳ Waiting for app to start (3–5 min for first build)…"
sleep 60

# Init the database
$SSH_CMD "cd ${APP_DIR} && sudo docker compose exec app python scripts/init_db.py"

echo ""
echo "================================================================"
echo "  ✅ Deployment complete!"
echo "================================================================"
echo ""
echo "  App URL:  http://${PUBLIC_IP}:8501"
echo "  Alt URL:  http://${PUBLIC_IP}"
echo ""
echo "  SSH access:"
echo "  ssh -i ~/.ssh/hastings-rag-key.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "  View logs:"
echo "  ssh -i ~/.ssh/hastings-rag-key.pem ubuntu@${PUBLIC_IP} \\"
echo "    'cd ${APP_DIR} && sudo docker compose logs -f'"
echo ""
echo "  DB password saved to: /tmp/hastings_db_password.txt"
echo "${DB_PASSWORD}" > /tmp/hastings_db_password.txt
echo "================================================================"
