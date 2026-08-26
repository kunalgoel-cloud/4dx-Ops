-- Phase 1 audit / exception treatment additions
create table if not exists data_quality_actions(
  id uuid primary key default gen_random_uuid(),
  issue_id uuid references data_quality_issues(id),
  action_type text not null,
  action_value jsonb,
  actor text,
  created_at timestamptz default now()
);

create table if not exists metric_calculation_runs(
  id uuid primary key default gen_random_uuid(),
  metric_code text not null,
  period_start date not null,
  period_end date not null,
  calculation_version text not null default 'phase1-v2',
  numerator numeric,
  denominator numeric,
  metric_value numeric,
  coverage_pct numeric,
  excluded_rows integer default 0,
  generated_at timestamptz default now()
);

create table if not exists metric_lineage(
  id uuid primary key default gen_random_uuid(),
  calculation_run_id uuid references metric_calculation_runs(id),
  source_table text not null,
  source_record_id text,
  contribution numeric,
  created_at timestamptz default now()
);
