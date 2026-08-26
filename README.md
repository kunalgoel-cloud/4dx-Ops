# Operations 4DX — Phase 1 v2

Streamlit + Supabase operations cockpit.

## UX changes in v2
- Individual metric trend cards with target lines instead of weekly scorecard.
- Separate Order→Ship and Ship→Delivery metrics.
- Clickable metric cards expose calculation data / evidence rows.
- Customer / City / SKU ranked drilldown is on the home page.
- Upload and data-quality handling are combined into Data Intake.
- New mapping values require explicit treatment: map, exclude, or historic mapping.
- Calculation window and coverage are visible.
- Lead → Lag relationships are shown explicitly.
- Mapping page rendering bug removed.
- Gemini is intentionally not connected in Phase 1.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SUPABASE_URL="https://kswjflivaquglmoeqehh.supabase.co"
export SUPABASE_KEY="YOUR_SUPABASE_KEY"
streamlit run app.py
```

For Streamlit Cloud, put SUPABASE_URL and SUPABASE_KEY in App Settings → Secrets.

## Supabase
Run SQL files in this order:
1. `sql/001_schema.sql`
2. `sql/002_views.sql`
3. `sql/003_phase1_audit.sql`

## GitHub push
From the repository root after copying these files:

```bash
git add -A
git status
git commit -m "Upgrade 4DX Ops cockpit and data intake"
git push origin main
```
