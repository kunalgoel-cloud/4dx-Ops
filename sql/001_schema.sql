create extension if not exists "pgcrypto";
create table if not exists system_settings(key text primary key,value jsonb not null,updated_at timestamptz default now());
create table if not exists metric_targets(id uuid primary key default gen_random_uuid(),metric_code text not null,scope_type text not null default 'global',scope_value text,direction text not null check(direction in('gte','lte','range')),target_value numeric,min_value numeric,max_value numeric,unit text,active boolean default true,updated_at timestamptz default now());
create table if not exists master_sku(standard_sku text primary key,sku_name text,active boolean default true,created_at timestamptz default now());
create table if not exists sku_mapping(id uuid primary key default gen_random_uuid(),source_system text not null,source_value text not null,standard_sku text references master_sku(standard_sku),conversion_factor numeric not null default 1,unit_type text not null default 'Individual units',active boolean default true,created_at timestamptz default now(),updated_at timestamptz default now(),unique(source_system,source_value));
create table if not exists master_customer(standard_customer text primary key,active boolean default true);
create table if not exists customer_mapping(id uuid primary key default gen_random_uuid(),source_system text not null,source_value text not null,standard_customer text references master_customer(standard_customer),active boolean default true,unique(source_system,source_value));
create table if not exists master_city(standard_city text primary key,active boolean default true);
create table if not exists city_mapping(id uuid primary key default gen_random_uuid(),source_system text not null,source_value text not null,standard_city text references master_city(standard_city),active boolean default true,unique(source_system,source_value));
create table if not exists master_courier(standard_courier text primary key,active boolean default true);
create table if not exists courier_mapping(id uuid primary key default gen_random_uuid(),source_system text not null,source_value text not null,standard_courier text references master_courier(standard_courier),active boolean default true,unique(source_system,source_value));
create table if not exists upload_runs(id uuid primary key default gen_random_uuid(),source_type text not null,filename text not null,file_hash text,reporting_period_start date,reporting_period_end date,status text not null,rows_received integer default 0,rows_accepted integer default 0,rows_rejected integer default 0,uploaded_at timestamptz default now(),uploaded_by text);
create table if not exists data_quality_issues(id uuid primary key default gen_random_uuid(),upload_run_id uuid references upload_runs(id),issue_type text not null,severity text not null,source_value text,row_reference text,message text not null,resolved boolean default false,created_at timestamptz default now());
create table if not exists raw_upload_rows(id uuid primary key default gen_random_uuid(),upload_run_id uuid references upload_runs(id),row_number integer,source_payload jsonb not null,accepted boolean default true,created_at timestamptz default now());
create table if not exists sales_orders(id uuid primary key default gen_random_uuid(),sales_order text,customer text,standard_customer text,sku text,standard_sku text,ordered_qty numeric,cancelled_qty numeric,order_date date,upload_run_id uuid references upload_runs(id));
create table if not exists invoice_lines(id uuid primary key default gen_random_uuid(),invoice_number text not null,sales_order text,customer text,standard_customer text,sku text,standard_sku text,quantity numeric,invoice_date date,upload_run_id uuid references upload_runs(id));
create table if not exists shipments(id uuid primary key default gen_random_uuid(),invoice_number text not null,awb text,sales_order text,customer text,standard_customer text,city text,standard_city text,courier text,standard_courier text,order_date timestamptz,dispatch_date timestamptz,delivery_date timestamptz,expected_delivery_date timestamptz,upload_run_id uuid references upload_runs(id));
create table if not exists shipment_lines(id uuid primary key default gen_random_uuid(),invoice_number text not null,awb text,sku text,standard_sku text,shipped_qty numeric,physical_weight numeric,weight_share numeric,allocated_cost numeric,upload_run_id uuid references upload_runs(id));
create table if not exists freight(id uuid primary key default gen_random_uuid(),awb text,invoice_number text,freight numeric,fuel numeric,oda numeric,other_charges numeric,total_charges numeric,chargeable_weight numeric,upload_run_id uuid references upload_runs(id));
create table if not exists purchase_orders(id uuid primary key default gen_random_uuid(),po_number text,supplier text,sku text,standard_sku text,ordered_qty numeric,received_qty numeric,po_date date,expected_delivery_date date,actual_receipt_date date,upload_run_id uuid references upload_runs(id));
create table if not exists inventory_snapshots(id uuid primary key default gen_random_uuid(),snapshot_date date not null,sku text,standard_sku text,total_stock numeric,batch text,expiry_date date,inventory_value numeric,upload_run_id uuid references upload_runs(id));
create table if not exists sales_daily(id uuid primary key default gen_random_uuid(),sales_date date not null,sku text,standard_sku text,units_sold numeric,upload_run_id uuid references upload_runs(id));
create table if not exists metric_daily(metric_date date not null,metric_code text not null,metric_value numeric,numerator numeric,denominator numeric,coverage_pct numeric,status text,primary key(metric_date,metric_code));
create index if not exists idx_shipments_invoice on shipments(invoice_number);
create index if not exists idx_shipments_awb on shipments(awb);
create index if not exists idx_shipments_customer_city on shipments(standard_customer,standard_city);
create index if not exists idx_shipment_lines_sku on shipment_lines(standard_sku);
create index if not exists idx_inventory_date_sku on inventory_snapshots(snapshot_date,standard_sku);
create index if not exists idx_sales_daily_date_sku on sales_daily(sales_date,standard_sku);
create index if not exists idx_metric_daily_code_date on metric_daily(metric_code,metric_date);
insert into system_settings(key,value) values
('shipment_definition','{"business_key":"invoice_number","technical_bridge":"awb"}'),
('fulfillment_definition','{"formula":"shipped_qty / ordered_qty","shipped_source":["outward_b2b","sales_b2c"]}'),
('drr_definition','{"period_days":30,"metric":"daily_run_rate"}'),
('inventory_definition','{"stock_unit":"individual_units","formula":"stock / drr"}'),
('cost_allocation','{"method":"weight_share"}'),
('supplier_otif','{"exclude_blank_edd":true}') on conflict(key) do nothing;
insert into metric_targets(metric_code,direction,target_value,unit) values
('fulfillment','gte',95,'%'),('otif','gte',95,'%'),('cost_per_shipment','lte',400,'INR'),('order_to_delivery','lte',5,'days'),('supplier_otif','gte',95,'%') on conflict do nothing;
