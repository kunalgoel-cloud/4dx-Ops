import os, hashlib, json
from typing import Optional

def get_supabase_client():
    from supabase import create_client
    url=os.getenv('SUPABASE_URL')
    key=os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    if not url or not key: return None
    return create_client(url,key)

def file_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def get_existing_uploads(client, source_type: str, sha: str):
    if not client: return []
    try:
        r=client.table('upload_runs').select('id,filename,status,file_hash,uploaded_at,rows_received').eq('source_type',source_type).eq('file_hash',sha).execute()
        return r.data or []
    except Exception:
        return []

def create_upload_run(client, source_type, filename, sha, start=None, end=None, rows=0, status='validated'):
    if not client: return None
    payload={'source_type':source_type,'filename':filename,'file_hash':sha,'reporting_period_start':start,'reporting_period_end':end,'status':status,'rows_received':rows}
    try:
        r=client.table('upload_runs').insert(payload).execute()
        return (r.data or [None])[0]
    except Exception:
        return None

def store_raw_rows(client, upload_run_id, df, accepted_mask=None):
    if not client or not upload_run_id or df is None: return 0
    if accepted_mask is None: accepted_mask=[True]*len(df)
    rows=[]
    for i,(_,row) in enumerate(df.iterrows(), start=1):
        payload={str(k): (None if row[k] != row[k] else row[k]) for k in df.columns}
        rows.append({'upload_run_id':upload_run_id,'row_number':i,'source_payload':payload,'accepted':bool(accepted_mask[i-1])})
    count=0
    for start in range(0,len(rows),500):
        try:
            r=client.table('raw_upload_rows').insert(rows[start:start+500]).execute(); count += len(r.data or [])
        except Exception:
            break
    return count
