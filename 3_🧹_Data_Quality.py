import streamlit as st
from src.demo_data import get_quality
st.set_page_config(page_title="Data Quality",page_icon="🧹",layout="wide")
st.title("Data Quality")
st.caption("Quality issues are surfaced instead of silently dropping records.")
a,b,c,d=st.columns(4); a.metric("Data quality score","97.4%"); b.metric("Rows received","1,842"); c.metric("Accepted","1,823"); d.metric("Issues","19")
st.progress(.974); st.subheader("Issue breakdown"); st.dataframe(get_quality(),use_container_width=True,hide_index=True)
st.info("Unavailable ≠ zero. Unresolved mappings are excluded from official metrics but remain visible. Raw uploads are retained.")
