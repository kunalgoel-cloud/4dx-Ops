import pandas as pd

REQUIRED={
 'sales':['Date','SKU','Units'],
 'inventory':['SKU','Total_Stock'],
 'sales_orders':['Sales Order'],
 'po':['PO Number'],
 'invoice':['Invoice Number'],
 'outward_b2b':['Invoice Number'],
 'tracking':['Invoice Number'],
 'freight':['Invoice Number']}

def validate_upload(file_obj, source):
    try:
        name=getattr(file_obj,'name','')
        if name.lower().endswith('.csv'): df=pd.read_csv(file_obj)
        else: df=pd.read_excel(file_obj)
    except Exception as e:
        return {'ok':False,'message':f'Could not read file: {e}','missing':[],'extra':[]}
    cols=[str(c).strip() for c in df.columns]
    df.columns=cols
    required=REQUIRED.get(source,[])
    missing=[c for c in required if c not in cols]
    return {'ok':not missing,'message':'accepted' if not missing else 'missing required columns','missing':missing,'extra':[],'rows':len(df),'preview':df}
