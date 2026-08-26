import os

def get_supabase_client():
    from supabase import create_client
    url=os.getenv('SUPABASE_URL')
    key=os.getenv('SUPABASE_KEY')
    if not url or not key: return None
    return create_client(url,key)
