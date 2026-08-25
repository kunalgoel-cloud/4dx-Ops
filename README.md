# Operations 4DX — Phase 1 UX Prototype

This version is intentionally **flat-layout** so it matches a GitHub repository where `app.py`, `demo_data.py`, `mapping.py`, `validation.py`, and `db.py` are all in the repository root.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud

Set these under **App → Settings → Secrets**:

```toml
SUPABASE_URL = "https://kswjflivaquglmoeqehh.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_KEY"
```

Do not commit the Supabase key to GitHub.

## Supabase

Run:
1. `sql/001_schema.sql`
2. `sql/002_views.sql`

## Current status

The dashboard is a UX prototype with representative dry-run values. Upload validation and mapping screens are present, but production ingestion/calculation is intentionally not wired yet.

## Why the import is flat

The first prototype used:

```python
from src.demo_data import get_demo_metrics
```

That requires a `src/` directory in the deployed repository. If files are uploaded to the GitHub root instead, Streamlit raises:

`ModuleNotFoundError: No module named 'src'`

This version uses root-level imports so the exact GitHub layout shown in the repository works.
