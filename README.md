# Operations 4DX — Phase 1 UX Prototype
Streamlit + Supabase architecture for the Operations 4DX scorecard.

Run:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Set `SUPABASE_URL` and `SUPABASE_KEY` as environment variables or Streamlit secrets. Never commit keys to GitHub.

The current UI uses representative dry-run values to validate UX. Upload validation/mapping are implemented as a prototype; production ingestion and metric calculation will be connected to Supabase next.
