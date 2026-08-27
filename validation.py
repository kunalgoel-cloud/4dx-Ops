import pandas as pd

REQUIRED={
 'sales':['Date','SKU','Units'], 'inventory':['SKU','Total_Stock'], 'sales_orders':['Sales Order'],
 'po':['PO Number'], 'invoice':['Invoice Number'], 'outward_b2b':['Invoice Number'], 'tracking':['Invoice Number'], 'freight':['Invoice Number']}
ALIASES={
 'sales':{'date':['Date','Sales Date','Sale Date'],'sku':['SKU','Item','Item Code'],'units':['Units','Quantity','Qty']},
 'inventory':{'sku':['SKU','Item','Item Code'],'total_stock':['Total_Stock','Stock','Total Stock']},
 'sales_orders':{'sales_order':['Sales Order','Sales Order Number','SO Number'],'sku':['SKU','Item','Item Code'],'ordered_qty':['Ordered Qty','Order Qty','Quantity','Qty'],'order_date':['Order Date','SO Date','Date']},
 'po':{'po_number':['PO Number','PO No','Purchase Order'],'sku':['SKU','Item','Item Code'],'po_date':['PO Date','Order Date','Date'],'expected_delivery_date':['Expected Delivery Date','EDD'],'actual_receipt_date':['Actual Receipt Date','Receipt Date','Supply Date']},
 'invoice':{'invoice_number':['Invoice Number','Invoice No','Invoice'],'invoice_date':['Invoice Date','Date'],'sku':['SKU','Item','Item Code'],'quantity':['Quantity','Qty','Invoiced Qty'],'customer':['Customer','Customer Name'],'invoice_value':['Invoice Value','Invoice Amount','Total']},
 'outward_b2b':{'invoice_number':['Invoice Number','Invoice No','Invoice'],'sku':['SKU','Item','Item Code'],'shipped_qty':['Shipped Qty','Quantity','Qty','Outward Qty']},
 'tracking':{'invoice_number':['Invoice Number','Invoice No','Invoice'],'ship_date':['Ship Date','Dispatch Date','Date of Ship'],'delivery_date':['Delivery Date','Delivered Date'],'city':['City'],'customer':['Customer','Customer Name']},
 'freight':{'invoice_number':['Invoice Number','Invoice No','Invoice'],'total_charges':['Total Charges','Total Charge','Billing Total'],'chargeable_weight':['Chargeable Weight','Chargeable_Weight','Billing Weight']},
}

def _read(file_obj):
    name=getattr(file_obj,'name','')
    if name.lower().endswith('.csv'): return pd.read_csv(file_obj)
    return pd.read_excel(file_obj)

def _find_col(cols, choices):
    norm={str(c).strip().lower():c for c in cols}
    for x in choices:
        if x.lower() in norm: return norm[x.lower()]
    return None

def validate_upload(file_obj, source):
    try: df=_read(file_obj)
    except Exception as e: return {'ok':False,'message':f'Could not read file: {e}','missing':[],'extra':[]}
    df.columns=[str(c).strip() for c in df.columns]
    aliases=ALIASES.get(source,{})
    mapped={k:_find_col(df.columns,v) for k,v in aliases.items()}
    required_keys=list(aliases)
    # Keep schema permissive: only the minimum identity column is mandatory for intake.
    min_required=REQUIRED.get(source,[])
    missing=[c for c in min_required if c not in df.columns and not any(v==c for v in mapped.values())]
    exact_missing=[]
    if missing: return {'ok':False,'message':'Missing minimum required columns','missing':missing,'extra':[],'rows':len(df),'preview':df,'mapped':mapped,'columns':list(df.columns)}
    duplicate_mask=df.duplicated(keep=False)
    exact_duplicates=int(duplicate_mask.sum())
    key_cols=[]
    if source in ('invoice','outward_b2b','tracking','freight'): key_cols=[mapped.get('invoice_number')]
    elif source=='sales_orders': key_cols=[mapped.get('sales_order')]
    elif source=='po': key_cols=[mapped.get('po_number')]
    elif source in ('sales','inventory'): key_cols=[mapped.get('sku')]
    key_cols=[c for c in key_cols if c]
    key_duplicate_rows=int(df.duplicated(subset=key_cols,keep=False).sum()) if key_cols else 0
    return {'ok':True,'message':'accepted','missing':exact_missing,'extra':[],'rows':len(df),'preview':df,'mapped':mapped,'columns':list(df.columns),'exact_duplicate_rows':exact_duplicates,'business_key_columns':key_cols,'business_duplicate_rows':key_duplicate_rows}
