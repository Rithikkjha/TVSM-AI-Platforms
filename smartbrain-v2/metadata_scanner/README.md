# Metadata Scanner — Steering File Generation

## Purpose

CLI tool that pulls full repository metadata from GitHub, generates
steering files (product.md, structure.md, tech.md), and triggers
re-ingestion into the Engineering Memory Graph.

Supports two modes:
- **Deterministic:** Template-based generation from raw metadata (fast, no LLM cost)
- **LLM-enhanced:** GPT-4o refines the templates into polished documentation

## Prerequisites

| Variable | Description |
|---|---|
| `GITHUB_TOKEN` | GitHub personal access token with repo read access |
| `AZURE_OPENAI_KEY` | Azure OpenAI API key (only needed with `--llm`) |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI endpoint (only needed with `--llm`) |

## Usage

### Scan a single repository

```bash
python -m metadata_scanner.run --repo booking-crud-services
```

### Scan all configured repositories

```bash
python -m metadata_scanner.run --all
```

### Use LLM-enhanced generation

```bash
python -m metadata_scanner.run --all --llm
```

### Verbose output

```bash
python -m metadata_scanner.run --all --verbose
```

## Configuration

- Repository list for `--all` is read from `config/mcp_servers.yaml`
  (the `github.config.repos` field)
- Output directory defaults to `kiro_steering/` (configurable via
  `KIRO_STEERING_DIR` env var)
- Neo4j and vector store credentials are read from the standard
  `config/settings.py` environment variables

## Output

```
kiro_steering/
├── booking-crud-services/
│   ├── product.md
│   ├── structure.md
│   └── tech.md
├── tvsm-auth/
│   ├── product.md
│   ├── structure.md
│   └── tech.md
└── ...
```
