import pandas as pd

def get_unmapped_items(source, df, mapped):
    out=[]
    if df is None: return pd.DataFrame(columns=['Type','Source Value','Reason'])
    for typ,colkey in [('SKU','sku'),('Customer','customer'),('City','city'),('Supplier','supplier')]:
        col=mapped.get(colkey) if mapped else None
        if col and col in df.columns:
            vals=df[col].dropna().astype(str).str.strip().unique()
            for v in vals[:100]: out.append([typ,v,f'New source value detected in {source} upload'])
    return pd.DataFrame(out,columns=['Type','Source Value','Reason']).drop_duplicates()

def get_unmapped_demo_items():
    return pd.DataFrame(columns=['Type','Source Value','Reason'])
