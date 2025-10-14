#!/bin/bash
PROJECT_ID=mineral-concord-474700-v2
SERVICE_NAME=aurelia-frontend
REGION=us-central1

gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --service-account aurelia-frontend-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --allow-unauthenticated