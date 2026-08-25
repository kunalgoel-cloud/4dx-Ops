create or replace view v_shipment_metrics as
select s.invoice_number,s.awb,s.standard_customer as customer,s.standard_city as city,s.standard_courier as courier,
extract(epoch from(s.dispatch_date-s.order_date))/86400.0 as order_to_ship_days,
extract(epoch from(s.delivery_date-s.dispatch_date))/86400.0 as ship_to_delivery_days,
extract(epoch from(s.delivery_date-s.order_date))/86400.0 as order_to_delivery_days,
case when s.delivery_date is not null and s.expected_delivery_date is not null then case when s.delivery_date<=s.expected_delivery_date then 1 else 0 end end as otif
from shipments s;
