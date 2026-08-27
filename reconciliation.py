"""Cross-source reconciliation.

Links independently-uploaded sources into one shipment-level view, per
the model already documented (but not implemented) in the Settings page:

    Shipment = one invoice number
    Shipped quantity = Outward B2B + Sales B2C reconstructed and matched
                        to Sales Orders

Join keys, using the canonical fields validation.py already extracts
into each source's `mapped` dict:
  - Invoice.sales_order  <-> Sales Orders.sales_order   (Sales Order Number)
  - Invoice.invoice_number <-> Outward B2B / Tracking / Freight.invoice_number

Nothing here silently drops a row on a failed match: every join reports
matched vs. total counts and a few unmatched-key examples, so gaps are
visible rather than absorbed into an average or a blank.
"""
import pandas as pd


def _key(series):
    return series.astype(str).str.strip()


def build_invoice_shipments(inv_df, inv_mapped):
    """Collapse a line-item Invoice export into one row per invoice
    (shipment identity) -- per README, 'one invoice = one shipment'."""
    inv_col = inv_mapped.get('invoice_number') or inv_mapped.get('invoice_id')
    if inv_df is None or inv_col is None or inv_col not in inv_df.columns:
        return pd.DataFrame()

    df = inv_df.copy()
    df['_invoice_key'] = _key(df[inv_col])

    rows = []
    for key, grp in df.groupby('_invoice_key', dropna=False):
        rec = {'Invoice Number': key, 'Invoice Line Items': len(grp)}
        for canon, label in [
            ('sales_order', 'Sales Order Number'),
            ('customer', 'Customer'),
            ('invoice_date', 'Invoice Date'),
            ('status', 'Invoice Status'),
        ]:
            col = inv_mapped.get(canon)
            if col and col in grp.columns and grp[col].notna().any():
                rec[label] = grp[col].dropna().iloc[0]
            else:
                rec[label] = None
        for canon, label in [
            ('invoice_value', 'Invoice Value'),
            ('quantity', 'Invoiced Qty'),
        ]:
            col = inv_mapped.get(canon)
            rec[label] = pd.to_numeric(grp[col], errors='coerce').sum() if col and col in grp.columns else None
        rows.append(rec)

    return pd.DataFrame(rows)


def _left_join_agg(shipments, key_col, other_df, other_mapped, other_key_canon, agg_map, label):
    """Left-join an aggregated other-source table onto shipments by a
    shared key, without ever dropping a shipment row. Returns
    (joined_df, matched, total, unmatched_examples, note)."""
    total = len(shipments)

    if other_df is None:
        out = shipments.copy()
        for _, out_label, _ in agg_map:
            out[out_label] = None
        return out, 0, total, [], f'No {label} data uploaded this session'

    other_key_col = other_mapped.get(other_key_canon)
    if other_key_col is None or other_key_col not in other_df.columns:
        out = shipments.copy()
        for _, out_label, _ in agg_map:
            out[out_label] = None
        return out, 0, total, [], f'{label} upload has no recognised join key'

    odf = other_df.copy()
    odf['_key'] = _key(odf[other_key_col])

    agg_rows = []
    for key, grp in odf.groupby('_key', dropna=False):
        rec = {'_key': key}
        for canon, out_label, how in agg_map:
            col = other_mapped.get(canon)
            if col is None or col not in grp.columns:
                rec[out_label] = None
                continue
            if how == 'sum':
                rec[out_label] = pd.to_numeric(grp[col], errors='coerce').sum()
            else:
                nn = grp[col].dropna()
                rec[out_label] = nn.iloc[0] if len(nn) else None
        agg_rows.append(rec)
    agg_df = pd.DataFrame(agg_rows) if agg_rows else pd.DataFrame(columns=['_key'] + [l for _, l, _ in agg_map])

    out = shipments.copy()
    out['_key'] = _key(out[key_col])
    merged = out.merge(agg_df, on='_key', how='left', indicator=True)
    matched = int((merged['_merge'] == 'both').sum())
    unmatched_examples = (
        merged.loc[merged['_merge'] == 'left_only', key_col]
        .dropna().astype(str).unique()[:5].tolist()
    )
    merged = merged.drop(columns=['_key', '_merge'])
    return merged, matched, total, unmatched_examples, None


def build_shipment_reconciliation(previews, mappeds):
    """previews / mappeds: dicts keyed by source name ('invoice',
    'sales_orders', 'outward_b2b', 'tracking', 'freight') mapping to the
    validated DataFrame / its `mapped` dict, for whichever sources were
    accepted this session. Missing sources are handled gracefully.

    Returns (shipment_df, stats) where stats is a list of per-link dicts
    (link name, matched count, total shipments, a few unmatched-key
    examples, and any blocking note) -- always shown, never silently
    dropped.
    """
    inv_df = previews.get('invoice')
    inv_mapped = mappeds.get('invoice', {})
    shipments = build_invoice_shipments(inv_df, inv_mapped)
    stats = []
    if shipments.empty:
        return shipments, stats

    so_df = previews.get('sales_orders')
    so_mapped = mappeds.get('sales_orders', {})
    if 'Sales Order Number' in shipments.columns and shipments['Sales Order Number'].notna().any():
        agg_map = [
            ('ordered_qty', 'Ordered Qty', 'sum'),
            ('order_date', 'Order Date', 'first'),
        ]
        shipments, matched, total, unmatched, note = _left_join_agg(
            shipments, 'Sales Order Number', so_df, so_mapped, 'sales_order', agg_map, 'Sales Orders'
        )
        stats.append({'link': 'Invoice → Sales Order', 'matched': matched, 'total': total,
                       'unmatched_examples': unmatched, 'note': note})
    else:
        stats.append({'link': 'Invoice → Sales Order', 'matched': 0, 'total': len(shipments),
                       'unmatched_examples': [], 'note': 'No Sales Order Number found on the Invoice upload'})

    for source_key, label, agg_map in [
        ('outward_b2b', 'Outward B2B', [('shipped_qty', 'Shipped Qty', 'sum')]),
        ('tracking', 'Tracking', [('ship_date', 'Ship Date', 'first'),
                                   ('delivery_date', 'Delivery Date', 'first'),
                                   ('city', 'City', 'first')]),
        ('freight', 'Freight', [('total_charges', 'Total Charges', 'sum'),
                                 ('chargeable_weight', 'Chargeable Weight', 'sum')]),
    ]:
        df = previews.get(source_key)
        mapped = mappeds.get(source_key, {})
        shipments, matched, total, unmatched, note = _left_join_agg(
            shipments, 'Invoice Number', df, mapped, 'invoice_number', agg_map, label
        )
        stats.append({'link': f'Invoice → {label}', 'matched': matched, 'total': total,
                       'unmatched_examples': unmatched, 'note': note})

    return shipments, stats
