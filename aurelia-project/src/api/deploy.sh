
#!/bin/bash

# AURELIA Deployment Script
# Using your GCP configuration

PROJECT_ID="mineral-concord-474700-v2"
REGION="us-central1"
SERVICE_NAME="aurelia-api"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
DB_CONNECTION="mineral-concord-474700-v2:us-central1:aurelia-db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Deploying AURELIA API to Cloud Run${NC}"
echo "================================================="
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo "Database: ${DB_CONNECTION}"
echo "================================================="

# Authenticate and set project
echo -e "${YELLOW}Setting up GCP authentication...${NC}"
gcloud config set project ${PROJECT_ID}

# Verify authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}Not authenticated. Please run: gcloud auth login${NC}"
    exit 1
fi

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com run.googleapis.com sqladmin.googleapis.com

# Build Docker image using Cloud Build
echo -e "${YELLOW}Building Docker image...${NC}"
gcloud builds submit --tag ${IMAGE_NAME} --timeout=1200s .

if [ $? -ne 0 ]; then
    echo -e "${RED}Docker build failed${NC}"
    exit 1
fi

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 10 \
    --timeout 300 \
    --allow-unauthenticated \
    --set-env-vars="PYTHONPATH=/app,INSTANCE_CONNECTION_NAME=${DB_CONNECTION},DB_USER=postgres,DB_PASSWORD=AureliaTeam2025,DB_NAME=aurelia_concepts,DB_HOST=127.0.0.1,DB_PORT=5432" \
    --add-cloudsql-instances ${DB_CONNECTION}

if [ $? -ne 0 ]; then
    echo -e "${RED}Deployment failed${NC}"
    exit 1
fi

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --platform managed \
    --region ${REGION} \
    --format 'value(status.url)')

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo "================================================="
echo -e "${GREEN}Service URL: ${SERVICE_URL}${NC}"
echo -e "${GREEN}API Docs: ${SERVICE_URL}/docs${NC}"
echo -e "${GREEN}Health Check: ${SERVICE_URL}/health${NC}"
echo -e "${GREEN}Stats: ${SERVICE_URL}/stats${NC}"
echo "================================================="

# Test the deployment
echo -e "${YELLOW}Testing deployment...${NC}"
sleep 10

echo "Testing health endpoint..."
if curl -f -s "${SERVICE_URL}/health" > /dev/null; then
    echo -e "${GREEN}Health check: PASSED${NC}"
else
    echo -e "${RED}Health check: FAILED${NC}"
fi

echo "Testing root endpoint..."
if curl -f -s "${SERVICE_URL}/" > /dev/null; then
    echo -e "${GREEN}Root endpoint: PASSED${NC}"
else
    echo -e "${RED}Root endpoint: FAILED${NC}"
fi

echo -e "${GREEN}AURELIA API deployment complete!${NC}"
echo "Save this URL for your team: ${SERVICE_URL}"
