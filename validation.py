import pandas as pd
EXPECTED={"sales":["SKU"],"inventory":["Total_Stock"],"sales_orders":["Sales Order"],"po":["PO"],"invoice":["Invoice Number"],"outward_b2b":["Invoice Number","AWB"],"tracking":["AWB"],"freight":["AWB","Total Charges"]}
def validate_upload(f,source):
    try:
        df=pd.read_csv(f) if f.name.lower().endswith(".csv") else pd.read_excel(f)
        cols={str(c).strip().lower():c for c in df.columns}
        missing=[x for x in EXPECTED.get(source,[]) if x.lower() not in cols]
        if missing:return {"ok":False,"message":f"This file does not match the {source.replace('_',' ')} schema.","missing":missing}
        return {"ok":True,"rows":len(df)}
    except Exception as e:return {"ok":False,"message":f"Could not read the file: {e}"}
