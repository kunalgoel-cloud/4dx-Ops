# Operations 4DX — Phase 1 v4

This version separates demo and production modes and adds upload-level duplicate protection.

## Production mode

The Home dashboard uses demo data only when there are no accepted production uploads. Once a valid upload is accepted, production mode is enabled and unavailable metrics remain `—`; demo data is never mixed with production data.

## Duplicate handling

- Exact file duplicates are detected with SHA-256 and blocked against previously accepted uploads of the same source type.
- Exact duplicate rows inside a file are reported.
- Source-specific business-key duplicates are reported for review rather than automatically deleted.
- Cross-source matching is not treated as duplication; e.g. an invoice may legitimately appear in Sales Orders and Outward B2B.

## Current limitation

v4 stages raw production uploads into Supabase and establishes the production-mode contract. The next step is the source-specific normalization/reconciliation engine that turns the staged rows into official metrics.
