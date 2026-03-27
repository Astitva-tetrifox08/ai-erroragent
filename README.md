# AI Error Notifier

An AI-powered production error analysis agent. When an exception occurs in any application monitored by Azure App Insights, this agent automatically identifies the source repository, fetches the relevant code, runs AI analysis to determine the root cause, and sends a detailed notification to Microsoft Teams.

## How It Works

```
Azure App Insights
        |
        | Exception detected
        v
Azure Alert Rule
        |
        | Webhook with exception dimensions
        | (ExceptionType, ExceptionMessage, FilePath, LineNumber)
        v
AI Error Notifier (Azure Web App)
        |
        |-- 1. Reads exception details from alert dimensions
        |-- 2. Resolves GitHub repo (name match or file search)
        |-- 3. Clones repo and fetches relevant code
        |-- 4. Sends code + error to AI (GitHub Models / GPT-4o-mini)
        |-- 5. Posts analysis to Microsoft Teams
        v
Microsoft Teams Channel
```

## Architecture

This agent is designed for environments where multiple applications report to a **shared App Insights** instance. Since many setups don't have `cloud_RoleName` configured per app, we take a different approach:

The **alert query** is configured to include exception details (type, message, file path, line number) as **split-by dimensions**. These dimensions are sent inside the webhook payload, so the agent can:

1. Read the `FilePath` from the alert dimensions
2. Use **GitHub Code Search API** to find which org repo contains that file
3. Clone the repo and fetch the specific file for AI analysis

This means no extra API keys or App Insights API queries are needed - everything comes through the alert webhook.

### Repo Resolution Strategy

The resolver tries these methods in order:

1. **Exact match** - alert project name matches a repo name in the org
2. **Partial match** - project name partially matches a repo name
3. **Service URL match** - domain in service URL matches a repo name
4. **GitHub Code Search** - searches for the exception file across all org repos

The repo list is fetched dynamically from the GitHub API on startup (no hardcoded config).

## Setup Guide

### 1. Azure Resources

Create the following resources:

| Resource | Purpose |
|----------|---------|
| Resource Group | Container for all resources |
| Container Registry (Basic SKU) | Stores the Docker image |
| Web App (Linux, Container, Basic B1) | Runs the agent |

### 2. Environment Variables

Set these in the Web App (Settings > Environment variables):

| Variable | Description |
|----------|-------------|
| `GITHUB_TOKEN` | Fine-grained PAT for the GitHub org (Contents: Read-only) |
| `GITHUB_ORG` | GitHub organization name |
| `GITHUB_MODELS_TOKEN` | Classic PAT for GitHub Models API (no scopes needed) |
| `TEAMS_WEBHOOK_URL` | Power Automate webhook URL for the Teams channel |
| `WEBSITES_PORT` | Set to `8000` |
| `LOG_LEVEL` | Optional. Default: `INFO`. Set to `DEBUG` for troubleshooting |

### 3. App Insights Alert Query

Configure a Log search alert rule in App Insights with this query:

```kusto
exceptions
| where outerMessage !contains "your-filtered-message-here"
| extend FilePath = tostring(customDimensions["code.file.path"])
| extend LineNumber = tostring(customDimensions["code.line.number"])
| project TimeGenerated = timestamp, OperationId = operation_Id, ExceptionType = outerType, ExceptionMessage = outerMessage, FilePath, LineNumber
| distinct OperationId, ExceptionType, ExceptionMessage, FilePath, LineNumber
```

Add these as **Split by dimensions** (all with "Include all future values" checked):
- `OperationId`
- `ExceptionType`
- `ExceptionMessage`
- `FilePath`
- `LineNumber`

### 4. Action Group

Create an action group with a **Webhook** action pointing to:
```
https://<your-web-app>.azurewebsites.net/azure/alert
```
Enable the **common alert schema**.

Attach this action group to the alert rule.

### 5. Teams Channel

Create a Teams channel and set up a workflow using the **"Send webhook alerts to a channel"** template. The webhook URL becomes your `TEAMS_WEBHOOK_URL`.

## Deployment

### Build and push

```bash
az acr build --registry <your-acr-name> --image ai-error-notifier:latest .
```

### Restart to pull new image

```bash
az webapp restart --name <your-web-app> --resource-group <your-rg>
```

## Project Structure

```
ai-error-notifier/
├── main.py                        # FastAPI app, webhook endpoint
├── Dockerfile                     # Container image definition
├── requirements.txt               # Python dependencies
├── repo_resolver/
│   └── resolver.py                # Resolves alert -> GitHub repo (dynamic + code search)
├── github/
│   ├── github_fetcher.py          # Clones repos, extracts code files
│   └── github_models_client.py    # AI analysis via GitHub Models API
├── notifiers/
│   └── teams_notifier.py          # Sends Adaptive Card to Teams via Power Automate
├── utils/
│   └── logger.py                  # Logging configuration
└── .env.example                   # Environment variable template
```

## Supported Languages

The code fetcher collects files with these extensions:
`.py`, `.cs`, `.ts`, `.js`, `.tsx`, `.jsx`, `.java`, `.go`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check. Returns `{"status": "running", "repos_loaded": N}` |
| `POST` | `/azure/alert` | Webhook endpoint for Azure Monitor alerts |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `repo_not_found` | Project name doesn't match any repo and no FilePath in alert | Verify alert query includes FilePath dimension |
| `no_code_found` | Repo has no supported code files | Add file extension to `github_fetcher.py` |
| `ai_failed` | GitHub Models token expired or invalid | Regenerate classic PAT |
| `teams_failed` | Power Automate webhook timeout or URL changed | Check webhook URL in Teams Workflows |
| `repos_loaded: 2` | GitHub PAT not approved for org or expired | Regenerate PAT and get org admin approval |

## Example: NVX-ai Deployment

This agent is currently deployed for the NVX-ai organization with the following configuration:

| Setting | Value |
|---------|-------|
| Web App | `ai-error-notifier` |
| Resource Group | `rg-ai-error-notifier-dev` |
| Container Registry | `aierrornotifieracr` |
| Region | West Europe |
| Pricing | Basic B1 ($13.14/month) |
| App Insights | `nvx-opex-ai` (shared across all NVX apps) |
| GitHub Org | `NVX-ai` (16 repos) |
| Teams Channel | AI Error Notifier |
| Alert Rule | `Exception Alert` (Log search, Sev1) |