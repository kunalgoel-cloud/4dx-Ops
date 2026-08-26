import pandas as pd

def get_unmapped_demo_items():
    return pd.DataFrame([
      ['SKU','8908024143123_75','New SKU from Sales upload'],
      ['Customer','New Customer Pvt Ltd','Customer not in master'],
      ['City','Gurugram NCR','City label not in master']],columns=['Type','Source Value','Reason'])
