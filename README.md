# product-research

A CLI agent tool that autonomously researches a specified product or service on the web and outputs a structured report covering overview, terms of service, privacy practices, and data security.

Uses Google Gemini API + Google Search Grounding (Vertex AI) for web research and structured extraction.

[日本語版 README はこちら](README.ja.md)

## Features

- **Autonomous web research** — Generates multiple search queries automatically to collect information including official documentation, ToS, and privacy policies
- **Structured JSON output** — Type-safe extraction via Pydantic schemas; directly usable by downstream tools
- **Data handling and security fields** — Dedicated fields for data collection, usage, sharing, encryption, authentication, and restrictions on sensitive data
- **Risk level assessment** — Three-tier overall risk rating: `low / medium / high`
- **Pipe-friendly** — `--json-only --no-save` outputs JSON to stdout for use with `jq` and other tools

## Installation

**Prerequisites:** Python 3.11+, [uv](https://docs.astral.sh/uv/), and a Google Cloud project with Vertex AI API enabled.

```bash
# Install as a CLI tool
uv tool install git+https://github.com/nlink-jp/product-research.git

# Or clone and install locally
git clone https://github.com/nlink-jp/product-research.git
cd product-research
uv tool install .
```

## Configuration

Requires a Google Cloud project and [gcloud CLI](https://cloud.google.com/sdk/docs/install) with Vertex AI API enabled.

```bash
gcloud auth application-default login
```

### Config file (recommended)

Create `~/.config/product-research/config.toml`:

```toml
[gcp]
project  = "your-project-id"
location = "us-central1"
```

A sample is provided in `config.example.toml`.

### Environment variables

Environment variables override the config file.

```bash
# Tool-specific (highest priority)
export PRODUCT_RESEARCH_PROJECT="your-project-id"
export PRODUCT_RESEARCH_LOCATION="us-central1"

# Cross-tool fallback
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"  # optional, defaults to us-central1
```

**Priority:** env vars > config.toml > defaults

## Usage

```bash
# Basic research
product-research "Slack"

# Specify output directory
product-research "ChatGPT" --output-dir ./reports

# Show verbose log (search queries, progress)
product-research "Notion" --verbose

# Output JSON only to stdout (no file save)
product-research "Dropbox" --json-only --no-save

# Combine with jq
product-research "GitHub Copilot" --json-only --no-save | jq '.data_security'
```

If not installed as a tool, you can also run directly:

```bash
uv run research_agent.py "Slack"
```

### Options

| Option | Short | Default | Description |
|---|---|---|---|
| `--output-dir` | `-o` | `./reports` | Report output directory |
| `--verbose` | `-v` | off | Show search queries and reference URLs |
| `--json-only` | — | off | Output JSON only to stdout |
| `--no-save` | — | off | Do not save files |

### Output format

Reports are saved under `./reports/`:

```
reports/
├── Slack_20260314_120000.md    # Markdown report
└── Slack_20260314_120000.json  # Structured JSON
```

The JSON schema includes: `overview`, `terms_of_service`, `user_data_handling`, `data_security`, `overall_risk_level`, `cautions`, and `sources`.

### Notes

- Research results are based on publicly available web information. Always verify the latest ToS and privacy policy on official sites.
- Fields where no information is found are reported as `"unknown"` — no guessing.
- Vertex AI costs apply (Gemini 2.5 Pro). Check your Google Cloud project billing.

## Building

```bash
# Type checking
uv run pyright
```

## Documentation

- [Development rules](./AGENTS.md)
