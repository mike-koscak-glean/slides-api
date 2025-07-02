# Slides Content API

A simple internal API service for reading and writing Google Slides content with formatting details, designed for integration with Glean agents.

## Overview

This FastAPI service provides two main endpoints:
- **Read**: Extract slide content and structure, identifying empty table cells for writing
- **Write**: Insert use cases into slide templates with proper formatting

## Features

- 🔍 **Read slide structure** and extract all content with positioning data
- 📝 **Write formatted use cases** to empty table cells
- 🎨 **Automatic formatting** with proper fonts, sizes, and styling
- 🔒 **Service account authentication** for secure Google Slides API access
- 📊 **Template-aware** cell identification and organization
- 🚀 **Cloud Run ready** with optimized Docker configuration

## Quick Start

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up service account:**
   - Place your `service-account.json` in this directory
   - Ensure it has Google Slides API permissions

3. **Run locally:**
   ```bash
   python main.py
   ```

4. **Test endpoints:**
   ```bash
   curl http://localhost:8080/
   ```

### Cloud Deployment

See [DEPLOYMENT.md](./DEPLOYMENT.md) for complete Google Cloud Run deployment instructions.

## API Endpoints

### GET `/`
Health check endpoint.

**Response:**
```json
{"message": "Slides Content API", "version": "1.0.0"}
```

### POST `/slides/read`
Read slide content and structure with object IDs for writing.

**Request:**
```json
{
  "document_id": "1gJ07qLdyubfQjl-VIqM3tle7g4CxtHsexLvLuvu5u0c"
}
```

**Response:**
```json
{
  "document_id": "1gJ07qLdyubfQjl-VIqM3tle7g4CxtHsexLvLuvu5u0c",
  "title": "Use Case Presentation",
  "total_slides": 6,
  "slides": [...],
  "empty_cells": {
    "slide_id": {
      "row1": {
        "description": "object_id",
        "department": "object_id",
        "impact": "object_id", 
        "data_sources": "object_id"
      }
    }
  }
}
```

### POST `/slides/write`
Write use cases to slide template with proper formatting.

**Request:**
```json
{
  "document_id": "1gJ07qLdyubfQjl-VIqM3tle7g4CxtHsexLvLuvu5u0c",
  "use_cases": [
    {
      "number": 8,
      "title": "Automated Meeting Documentation",
      "description": "Sales teams struggle with documentation. Glean automates summaries.",
      "department": "Sales & Customer Success",
      "impact": "Accelerate sales cycles and improve follow-up consistency.",
      "data_sources": "Gong, Salesforce, Email, Teams",
      "weekly_time_saved": "3-4 hours"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully wrote 1 use cases to slides",
  "use_cases_written": 1,
  "document_url": "https://docs.google.com/presentation/d/..."
}
```

## Glean Integration

### OpenAPI Specifications

Individual OAS specs for Glean integration:
- [`read-slides-oas.yaml`](./read-slides-oas.yaml) - Read endpoint specification
- [`write-slides-oas.yaml`](./write-slides-oas.yaml) - Write endpoint specification

### Agent Prompt

See [`GLEAN_AGENT_PROMPT.md`](./GLEAN_AGENT_PROMPT.md) for the comprehensive prompt template that guides the Glean agent through:
1. Analyzing call transcripts
2. Reading template formatting guidelines
3. Processing use case examples
4. Generating formatted use cases
5. Creating API-ready JSON output

### Template Format

[`static/template-format.json`](./static/template-format.json) contains detailed formatting specifications including:
- Font requirements (Arial, 8pt bold titles, 7pt descriptions)
- Column structure and content guidelines
- Quality standards and consistency rules
- Character limits and formatting patterns

## Content Guidelines

### Use Case Structure
Each use case follows this pattern:
- **Title**: Concise, actionable (5-12 words)
- **Description**: Problem + Glean solution (2-3 sentences)
- **Department**: Primary beneficiary
- **Impact**: Business value and rationale
- **Data Sources**: Relevant systems (3-5 sources)

### Formatting Standards
- **Title**: 8pt Arial Bold, format "{number}. {title}"
- **Description**: 7pt Arial Regular, max 500 characters
- **Department**: 8pt Arial Regular, max 50 characters  
- **Impact**: 7pt Arial Regular, max 300 characters
- **Data Sources**: 8pt Arial Regular, comma-separated, max 100 characters

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Glean Agent   │───▶│  Slides API     │───▶│ Google Slides   │
│                 │    │  (Cloud Run)    │    │      API        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │
        ▼                       │
┌─────────────────┐             │
│ Static Resources│             │
│ • Template      │             │
│ • Use Cases CSV │             │
│ • Call Transcript│            │
└─────────────────┘             │
                                ▼
                    ┌─────────────────┐
                    │ Service Account │
                    │ Authentication  │
                    └─────────────────┘
```

## Security

- Service account authentication with minimal permissions
- No sensitive data stored in containers
- HTTPS-only communication
- Request timeouts and resource limits

## Monitoring

- Health check endpoint at `/`
- Structured logging for debugging
- Cloud Run automatic metrics and alerting
- Request timeout: 300 seconds

## File Structure

```
slides-api/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── README.md              # This file
├── DEPLOYMENT.md          # Deployment instructions
├── GLEAN_AGENT_PROMPT.md  # LLM prompt template
├── read-slides-oas.yaml   # Read endpoint OAS spec
├── write-slides-oas.yaml  # Write endpoint OAS spec
├── static/
│   └── template-format.json # Formatting guidelines
└── service-account.json   # Google API credentials (not in repo)
```

## Development

### Adding New Features

1. **Template Changes**: Update `static/template-format.json`
2. **API Changes**: Update both `main.py` and OAS specs
3. **Prompt Updates**: Modify `GLEAN_AGENT_PROMPT.md`

### Testing

```bash
# Run locally
python main.py

# Test read endpoint
curl -X POST http://localhost:8080/slides/read \
  -H "Content-Type: application/json" \
  -d '{"document_id": "your-doc-id"}'

# Test write endpoint  
curl -X POST http://localhost:8080/slides/write \
  -H "Content-Type: application/json" \
  -d @test-use-cases.json
```

## Support

For deployment issues or API questions, refer to:
- [DEPLOYMENT.md](./DEPLOYMENT.md) for Cloud Run setup
- [GLEAN_AGENT_PROMPT.md](./GLEAN_AGENT_PROMPT.md) for agent configuration
- Google Cloud Run documentation for infrastructure questions