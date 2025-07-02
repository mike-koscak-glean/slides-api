# Google Cloud Run Deployment Instructions

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Cloud Run API** enabled
3. **Google Slides API** enabled  
4. **Service Account** with Google Slides API access

## Service Account Setup

1. Go to **IAM & Admin > Service Accounts** in GCP Console
2. Create new service account named `slides-api-service`
3. Grant roles:
   - `roles/run.invoker` (for Cloud Run access)
   - Custom role with `slides.presentations.readonly` and `slides.presentations.readwrite` permissions
4. Create and download JSON key file
5. Rename the key file to `service-account.json`

## Deployment Steps (GCP UI)

### Step 1: Upload Service Account Key

1. In your local `slides-api/` folder, place your `service-account.json` file
2. Ensure the file is included in the build (Dockerfile copies all files)

### Step 2: Deploy to Cloud Run

1. **Navigate to Cloud Run** in GCP Console
2. Click **"Create Service"**
3. **Select "Deploy one revision from an existing container image"**
4. Click **"Set up with Cloud Build"**

### Step 3: Configure Cloud Build

1. **Repository**: Choose your Git repository (or upload via Source Repository)
2. **Build Type**: Dockerfile
3. **Dockerfile location**: `/slides-api/Dockerfile`
4. **Build context**: `/slides-api/`

### Step 4: Service Configuration

```
Service Name: slides-content-api
Region: us-central1 (or your preferred region)
Authentication: Require authentication
CPU allocation: CPU is only allocated during request processing
Ingress: Allow all traffic
Port: 8080
```

### Step 5: Container Configuration

```
Memory: 1 GiB
CPU: 1
Request timeout: 300 seconds
Maximum requests per container: 100
```

### Step 6: Environment Variables

Add these environment variables:

```
GOOGLE_SERVICE_ACCOUNT_FILE=/app/service-account.json
PYTHONPATH=/app
PYTHONUNBUFFERED=1
```

### Step 7: Deploy

1. Click **"Create"** to deploy
2. Wait for deployment to complete (3-5 minutes)
3. Note the service URL (e.g., `https://slides-content-api-xxx-uc.a.run.app`)

## Post-Deployment Configuration

### Update OAS Specs

1. Update both OAS files with your actual Cloud Run URL:
   - `read-slides-oas.yaml` 
   - `write-slides-oas.yaml`

Replace:
```yaml
servers:
  - url: https://your-cloud-run-service-url
```

With:
```yaml
servers:
  - url: https://slides-content-api-xxx-uc.a.run.app
```

### Test Deployment

Test the health endpoint:
```bash
curl https://your-service-url.run.app/
```

Expected response:
```json
{"message": "Slides Content API", "version": "1.0.0"}
```

## Security Considerations

1. **Service Account Permissions**: Only grant minimum required permissions
2. **Cloud Run Authentication**: Keep authentication required
3. **API Access**: Control access via IAM roles
4. **Secrets Management**: Consider using Google Secret Manager for production

## Monitoring & Logs

1. **Cloud Run Logs**: View in GCP Console > Cloud Run > Service > Logs
2. **Health Checks**: Configured automatically (checks `/` endpoint)
3. **Metrics**: Available in Cloud Run monitoring dashboard

## Cost Optimization

- **CPU allocation**: "CPU is only allocated during request processing"
- **Scaling**: Default 0-100 instances (scales to zero when not in use)
- **Memory**: 1 GiB is sufficient for this workload

## Troubleshooting

### Common Issues

1. **Service Account Access**: Ensure the service account has proper Slides API permissions
2. **File Not Found**: Verify `service-account.json` is in the container
3. **Memory Issues**: Increase memory if processing large presentations
4. **Timeout**: Increase request timeout for large slide operations

### Logs Commands

View recent logs:
```bash
gcloud run services logs read slides-content-api --region=us-central1
```

### Update Service

For updates, redeploy using the same Cloud Build process or use:
```bash
gcloud run deploy slides-content-api --source=./slides-api --region=us-central1
```

## Integration with Glean

1. **Upload OAS specs** to Glean with the updated Cloud Run URLs
2. **Configure authentication** in Glean using service account or IAM
3. **Test endpoints** from Glean agent to ensure connectivity

The API is now ready for integration with your Glean agent!