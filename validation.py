import pandas as pd

REQUIRED = {
    'sales': ['Date', 'SKU', 'Units'],
    'inventory': ['SKU', 'Total_Stock'],
    'sales_orders': ['Sales Order'],
    'po': ['PO Number'],
    'invoice': ['Invoice Number'],
    'outward_b2b': ['Invoice Number'],
    'tracking': ['Invoice Number'],
    'freight': ['Invoice Number'],
}

ALIASES = {
    'sales': {
        'date': ['Date', 'Sales Date', 'Sale Date'],
        'sku': ['SKU', 'Item', 'Item Code'],
        'units': ['Units', 'Quantity', 'Qty', 'Quantity Sold', 'quantity_sold'],
    },
    'inventory': {
        'sku': ['SKU', 'Item', 'Item Code'],
        'total_stock': ['Total_Stock', 'Stock', 'Total Stock'],
        'product_title': ['Title', 'Product Title', 'Product Name', 'Item Name'],
    },
    'sales_orders': {
        'sales_order': ['Sales Order', 'Sales Order Number', 'SO Number'],
        'sku': ['SKU', 'Item', 'Item Code'],
        'ordered_qty': ['Ordered Qty', 'Order Qty', 'Quantity', 'Qty'],
        'order_date': ['Order Date', 'SO Date', 'Date'],
    },
    'po': {
        'po_number': ['PO Number', 'PO No', 'Purchase Order'],
        'sku': ['SKU', 'Item', 'Item Code'],
        'po_date': ['PO Date', 'Order Date', 'Date'],
        'expected_delivery_date': ['Expected Delivery Date', 'EDD'],
        'actual_receipt_date': ['Actual Receipt Date', 'Receipt Date', 'Supply Date'],
    },
    'invoice': {
        'invoice_number': ['Invoice Number', 'Invoice No', 'Invoice', 'Invoice #'],
        'invoice_id': ['Invoice ID', 'Invoice Id', 'ID'],
        'invoice_date': ['Invoice Date', 'Date'],
        'sku': ['SKU', 'Item', 'Item Code'],
        'quantity': ['Quantity', 'Qty', 'Invoiced Qty'],
        'customer': ['Customer', 'Customer Name'],
        'invoice_value': ['Invoice Value', 'Invoice Amount', 'Total', 'Grand Total'],
        'status': ['Invoice Status', 'Status'],
    },
    'outward_b2b': {
        'invoice_number': ['Invoice Number', 'Invoice No', 'Invoice', 'Invoice #'],
        'sku': ['SKU', 'Item', 'Item Code'],
        'shipped_qty': ['Shipped Qty', 'Quantity', 'Qty', 'Outward Qty'],
    },
    'tracking': {
        'invoice_number': ['Invoice Number', 'Invoice No', 'Invoice', 'Invoice #'],
        'ship_date': ['Ship Date', 'Dispatch Date', 'Date of Ship'],
        'delivery_date': ['Delivery Date', 'Delivered Date'],
        'city': ['City'],
        'customer': ['Customer', 'Customer Name'],
    },
    'freight': {
        'invoice_number': ['Invoice Number', 'Invoice No', 'Invoice', 'Invoice #'],
        'total_charges': ['Total Charges', 'Total Charge', 'Billing Total'],
        'chargeable_weight': ['Chargeable Weight', 'Chargeable_Weight', 'Billing Weight'],
    },
}


def _read(file_obj):
    name = getattr(file_obj, 'name', '') or ''
    if name.lower().endswith('.csv'):
        return pd.read_csv(file_obj)
    if name.lower().endswith(('.xlsx', '.xls')):
        return pd.read_excel(file_obj)
    # No usable filename (e.g. the caller re-wrapped the bytes in a bare
    # BytesIO): sniff the content instead of guessing Excel by default.
    file_obj.seek(0)
    try:
        df = pd.read_csv(file_obj)
        file_obj.seek(0)
        return df
    except Exception:
        file_obj.seek(0)
        return pd.read_excel(file_obj)


def _clean_columns(df):
    df = df.copy()
    df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]
    return df


def _normalize_variants(raw):
    cleaned = str(raw).replace('\ufeff', '').strip()
    variants = {cleaned.lower()}
    # BI/reporting-tool exports often qualify columns as "Table.Column"
    # (e.g. "Inventory_Snapshots.Total_Stock"). Match on the part after
    # the last dot too, so aliases still resolve against the real field.
    if '.' in cleaned:
        variants.add(cleaned.split('.')[-1].strip().lower())
    # Zoho-style exports commonly use a trailing '#' for "Number"
    # (e.g. "Sales Order#", "PO#", "Invoice#"). Match with it stripped too.
    if '#' in cleaned:
        variants.add(cleaned.replace('#', '').strip().lower())
    return variants


def _find_col(cols, choices):
    norm = {}
    for c in cols:
        for v in _normalize_variants(c):
            norm.setdefault(v, c)
    for x in choices:
        for v in _normalize_variants(x):
            if v in norm:
                return norm[v]
    return None


def _duplicate_summary(df, source, mapped):
    """Return duplicate diagnostics without treating invoice line items as duplicates.

    Zoho-style invoice exports are line-item exports: one invoice can legitimately
    occupy many rows. Therefore Invoice Number alone is an invoice/entity key, not
    a row-level duplicate key.
    """
    exact_duplicate_rows = int(df.duplicated(keep=False).sum())
    key_cols = []
    business_duplicate_rows = 0
    business_duplicate_note = ''
    entity_count = None

    if source == 'invoice':
        inv_col = mapped.get('invoice_number') or mapped.get('invoice_id')
        sku_col = mapped.get('sku')
        if inv_col:
            entity_count = int(df[inv_col].dropna().astype(str).str.strip().nunique())
            # Multiple rows for the same invoice are expected when the source is
            # line-item level. Do NOT flag these as duplicate uploads.
            business_duplicate_note = (
                f'{entity_count:,} unique invoice identifiers across {len(df):,} line rows. '
                'Multiple rows per invoice are treated as line items, not duplicate invoices.'
            )
            if sku_col:
                key_cols = [inv_col, sku_col]
                # Only use this as a diagnostic. It does not reject the upload.
                business_duplicate_rows = int(df.duplicated(subset=key_cols, keep=False).sum())
        return exact_duplicate_rows, business_duplicate_rows, key_cols, entity_count, business_duplicate_note

    if source in ('outward_b2b', 'tracking', 'freight'):
        c = mapped.get('invoice_number')
        if c:
            key_cols = [c]
    elif source == 'sales_orders':
        c = mapped.get('sales_order')
        if c:
            key_cols = [c]
    elif source == 'po':
        c = mapped.get('po_number')
        if c:
            key_cols = [c]
    elif source in ('sales', 'inventory'):
        c = mapped.get('sku')
        if c:
            key_cols = [c]

    if key_cols:
        business_duplicate_rows = int(df.duplicated(subset=key_cols, keep=False).sum())

    return exact_duplicate_rows, business_duplicate_rows, key_cols, entity_count, business_duplicate_note


def validate_upload(file_obj, source, date_override=None):
    try:
        df = _clean_columns(_read(file_obj))
    except Exception as e:
        return {
            'ok': False,
            'message': f'Could not read file: {e}',
            'missing': [],
            'extra': [],
            'rows': 0,
        }

    # Some source-system exports are aggregated reports with no per-row date
    # at all (e.g. a "Sales by Item" summary). When the uploader has no Date
    # column, allow the caller to supply the reporting month/date explicitly
    # and stamp it onto every row rather than rejecting the file outright.
    date_injected = False
    if source == 'sales' and date_override is not None:
        existing_date_col = _find_col(df.columns, ALIASES.get('sales', {}).get('date', ['Date']))
        if existing_date_col is None:
            df['Date'] = pd.to_datetime(date_override).strftime('%Y-%m-%d')
            date_injected = True

    aliases = ALIASES.get(source, {})
    mapped = {k: _find_col(df.columns, v) for k, v in aliases.items()}

    # Minimum identity validation is alias-aware: a required column like
    # "Units" is satisfied if any of its known aliases (e.g. "quantity_sold")
    # was matched into the canonical field, not just an exact name match.
    min_required = REQUIRED.get(source, [])
    missing = []
    sku_identity_source = None
    for required in min_required:
        found = _find_col(df.columns, [required])
        if found is not None:
            if source == 'inventory' and required == 'SKU':
                sku_identity_source = 'sku'
            continue
        if source == 'invoice' and (mapped.get('invoice_number') or mapped.get('invoice_id')):
            continue
        canonical_key = required.lower().replace(' ', '_')
        if mapped.get(canonical_key) is not None:
            if source == 'inventory' and required == 'SKU':
                sku_identity_source = 'sku'
            continue
        # Some inventory exports (BI/reporting-tool "tabular view" style)
        # carry no coded SKU at all, only a product Title. Accept the file
        # using Title as a stand-in identity rather than hard-rejecting it,
        # but this is flagged in the result so it's never silently treated
        # as equivalent to a real SKU (cross-source SKU joins won't apply
        # until it's manually mapped).
        if source == 'inventory' and required == 'SKU' and mapped.get('product_title') is not None:
            sku_identity_source = 'title'
            continue
        missing.append(required)

    if missing:
        return {
            'ok': False,
            'message': 'Missing minimum required columns',
            'missing': missing,
            'extra': [],
            'rows': len(df),
            'preview': df,
            'mapped': mapped,
            'columns': list(df.columns),
        }

    exact_duplicate_rows, business_duplicate_rows, key_cols, entity_count, business_duplicate_note = _duplicate_summary(
        df, source, mapped
    )

    result = {
        'ok': True,
        'message': 'accepted',
        'missing': [],
        'extra': [],
        'rows': len(df),
        'preview': df,
        'mapped': mapped,
        'columns': list(df.columns),
        'exact_duplicate_rows': exact_duplicate_rows,
        'business_key_columns': key_cols,
        'business_duplicate_rows': business_duplicate_rows,
    }

    if source == 'sales':
        result['date_injected'] = date_injected
        if date_injected:
            result['date_injected_value'] = str(pd.to_datetime(date_override).date())

    if source == 'inventory':
        result['sku_identity_source'] = sku_identity_source

    if source == 'invoice':
        result['entity_count'] = entity_count
        result['business_duplicate_note'] = business_duplicate_note
        result['is_line_item_export'] = bool(entity_count and entity_count < len(df))

    return result
