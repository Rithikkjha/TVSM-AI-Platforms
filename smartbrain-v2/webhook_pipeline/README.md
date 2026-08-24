# Webhook Pipeline — Automated Steering Updates

## Purpose

Receives GitHub PR webhook events, analyzes diffs with GPT-4o, and
automatically updates the service's steering files (product.md,
structure.md, tech.md) when material changes are detected.

## Prerequisites

| Variable | Description |
|---|---|
| `STEERING_WEBHOOK_SECRET` | HMAC-SHA256 shared secret for webhook signature validation |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint URL |
| `GITHUB_TOKEN` | GitHub personal access token for API calls |

## Usage

### Start the webhook server

```bash
./start.sh webhook
# Or directly:
uvicorn webhook_pipeline.app:app --host 0.0.0.0 --port 8002 --reload
```

### Endpoint

```
POST /webhooks/steering
```

### Configure GitHub Webhook

1. Go to your repo → Settings → Webhooks → Add webhook
2. **Payload URL:** `https://your-host:8002/webhooks/steering`
3. **Content type:** `application/json`
4. **Secret:** The value of your `STEERING_WEBHOOK_SECRET` env var
5. **Events:** Select "Pull requests"

### Response Schema

```json
{
  "status": "updated | no_changes | error",
  "repo": "repo-name",
  "updated_files": ["product", "tech"],
  "reasoning": "Added new payment gateway dependency...",
  "ingestion": {
    "files_processed": 2,
    "files_skipped": 1,
    "chunks_created": 2,
    "error": null
  }
}
```

## Configuration

All configuration is via environment variables (or `.env` file),
managed by `config/settings.py`. Key settings:

- `STEERING_WEBHOOK_SECRET` — HMAC secret for signature validation
- `KIRO_STEERING_DIR` — output directory for steering files (default: `kiro_steering`)
- `AZURE_OPENAI_DEPLOYMENT_GPT4O` — GPT-4o deployment name for analysis
