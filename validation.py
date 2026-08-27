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
        'units': ['Units', 'Quantity', 'Qty'],
    },
    'inventory': {
        'sku': ['SKU', 'Item', 'Item Code'],
        'total_stock': ['Total_Stock', 'Stock', 'Total Stock'],
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
    name = getattr(file_obj, 'name', '')
    if name.lower().endswith('.csv'):
        return pd.read_csv(file_obj)
    return pd.read_excel(file_obj)


def _clean_columns(df):
    df = df.copy()
    df.columns = [str(c).replace('\ufeff', '').strip() for c in df.columns]
    return df


def _find_col(cols, choices):
    norm = {str(c).replace('\ufeff', '').strip().lower(): c for c in cols}
    for x in choices:
        key = str(x).replace('\ufeff', '').strip().lower()
        if key in norm:
            return norm[key]
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


def validate_upload(file_obj, source):
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

    aliases = ALIASES.get(source, {})
    mapped = {k: _find_col(df.columns, v) for k, v in aliases.items()}

    # Minimum identity validation is alias-aware. This fixes exports such as the
    # current Zoho invoice CSV where the actual column is "Invoice Number".
    min_required = REQUIRED.get(source, [])
    missing = []
    for required in min_required:
        found = _find_col(df.columns, [required])
        if found is None:
            # Also allow any mapped canonical field to satisfy the requirement.
            if source == 'invoice' and (mapped.get('invoice_number') or mapped.get('invoice_id')):
                continue
            if not any(v == required for v in mapped.values()):
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

    if source == 'invoice':
        result['entity_count'] = entity_count
        result['business_duplicate_note'] = business_duplicate_note
        result['is_line_item_export'] = bool(entity_count and entity_count < len(df))

    return result
