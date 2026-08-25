import pandas as pd
def get_unmapped_demo_items():
    return pd.DataFrame([["SKU","8908024143123_75","—","🔴 Mapping required"],["Customer","New Customer Pvt Ltd","—","🔴 Mapping required"],["City","Gurugram NCR","Gurugram","🟢 Suggested"]],columns=["Type","Source Value","Suggested Standard Value","Status"])
