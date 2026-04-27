# envoy-drift

> A CLI tool that detects configuration drift between environment files across staging and production deployments.

---

## Installation

```bash
pip install envoy-drift
```

Or install from source:

```bash
git clone https://github.com/your-org/envoy-drift.git && cd envoy-drift && pip install .
```

---

## Usage

Compare two environment files and surface any configuration drift:

```bash
envoy-drift compare --staging .env.staging --production .env.production
```

**Example output:**

```
[DRIFT DETECTED]
  + API_TIMEOUT     staging=30   production=60
  - CACHE_ENABLED   staging=true production=(missing)
  ~ LOG_LEVEL       staging=debug production=info

3 drift(s) found across 2 environment files.
```

### Options

| Flag | Description |
|------|-------------|
| `--staging` | Path to the staging environment file |
| `--production` | Path to the production environment file |
| `--ignore` | Comma-separated list of keys to ignore |
| `--output` | Output format: `text` (default), `json`, or `csv` |

```bash
# Ignore specific keys and export as JSON
envoy-drift compare --staging .env.staging --production .env.production \
  --ignore APP_NAME,VERSION --output json
```

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.

---

## License

[MIT](LICENSE)